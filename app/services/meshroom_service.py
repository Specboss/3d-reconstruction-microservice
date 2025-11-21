"""Meshroom reconstruction service."""

from __future__ import annotations

import asyncio
import shlex
import uuid
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from app.core.logger import get_logger
from app.core.settings import MeshroomConfigModel
from app.core.storage.base.storage import BaseStorage

JobStatus = Literal["pending", "downloading", "processing", "uploading", "completed", "failed"]


class MeshroomService:
    """Service for managing Meshroom 3D reconstruction jobs."""

    def __init__(
        self,
        config: MeshroomConfigModel,
        storage: BaseStorage,
    ) -> None:
        """
        Initialize Meshroom service.

        Args:
            config: Meshroom configuration
            storage: Storage provider for files
        """
        self.config = config
        self.storage = storage
        self.workspace_root = Path(config.workspace_dir)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(self.__class__.__name__)

    async def process_job(
        self,
        model_id: int,
        images_zip_url: str,
    ) -> tuple[JobStatus, str | None]:
        """
        Process a reconstruction job.

        Args:
            model_id: Model identifier
            images_zip_url: URL to ZIP archive with images

        Returns:
            Tuple of (final_status, result_url_or_error)
        """
        job_dir = self.workspace_root / f"model_{model_id}"
        zip_path = job_dir / "photos.zip"
        images_dir = job_dir / "images"
        cache_dir = job_dir / "cache"
        output_dir = job_dir / "output"

        try:
            # Create directories
            for directory in (job_dir, images_dir, cache_dir, output_dir):
                directory.mkdir(parents=True, exist_ok=True)

            # Download and extract ZIP
            self.logger.info("Model %s: Downloading ZIP from %s", model_id, images_zip_url)
            await self.storage.download_url(images_zip_url, zip_path)
            
            self.logger.info("Model %s: Extracting images", model_id)
            await self._extract_zip(zip_path, images_dir)

            # Run Meshroom
            self.logger.info("Model %s: Starting Meshroom processing", model_id)
            await self._run_meshroom(model_id, images_dir, cache_dir, output_dir)

            # Upload results as GLTF
            self.logger.info("Model %s: Uploading results", model_id)
            result_url = await self._upload_results(model_id, output_dir)

            self.logger.info("Model %s: Completed successfully", model_id)
            return "completed", result_url

        except Exception as exc:
            self.logger.error("Model %s: Failed with error: %s", model_id, exc, exc_info=True)
            return "failed", str(exc)

        finally:
            # Cleanup workspace
            await self._cleanup_workspace(job_dir)

    async def _extract_zip(self, zip_path: Path, target_dir: Path) -> None:
        """Extract ZIP archive to target directory."""
        import zipfile
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        
        # Count extracted images
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
        image_count = sum(
            1 for f in target_dir.rglob('*')
            if f.is_file() and f.suffix.lower() in image_extensions
        )
        
        self.logger.info("Extracted %d images from ZIP", image_count)

    async def _run_meshroom(
        self,
        model_id: int,
        images_dir: Path,
        cache_dir: Path,
        output_dir: Path,
    ) -> None:
        """Execute Meshroom binary for reconstruction."""
        command = [
            self.config.binary,
            "--pipeline",
            self.config.pipeline_path,
            "--input",
            str(images_dir),
            "--cache",
            str(cache_dir),
            "--output",
            str(output_dir),
        ]

        self.logger.info("Model %s: Running command: %s", model_id, shlex.join(command))

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.resources.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.wait()
            raise RuntimeError(
                f"Meshroom processing timed out after {self.config.resources.timeout_seconds}s"
            ) from exc

        if stdout:
            self.logger.debug("Model %s stdout: %s", model_id, stdout.decode())
        if stderr:
            self.logger.warning("Model %s stderr: %s", model_id, stderr.decode())

        if process.returncode != 0:
            raise RuntimeError(
                f"Meshroom process failed with exit code {process.returncode}"
            )

    async def _upload_results(self, model_id: int, output_dir: Path) -> str:
        """Upload reconstruction results to storage as GLTF."""
        # Find the main output file (prefer .gltf, fallback to .obj)
        gltf_files = list(output_dir.rglob("*.gltf")) + list(output_dir.rglob("*.glb"))
        obj_files = list(output_dir.rglob("*.obj"))
        
        if gltf_files:
            main_file = gltf_files[0]
        elif obj_files:
            # TODO: Convert OBJ to GLTF using obj2gltf or similar
            main_file = obj_files[0]
            self.logger.warning(
                "Model %s: Found OBJ file, GLTF conversion not implemented yet",
                model_id,
            )
        else:
            raise FileNotFoundError("No output model file (.gltf/.glb/.obj) found")

        # Upload main model file
        remote_key = f"models/model_{model_id}/model.gltf"
        result_url = await self.storage.upload_file(main_file, remote_key)
        
        # Upload textures if present
        texture_files = list(output_dir.rglob("*.png")) + list(output_dir.rglob("*.jpg"))
        for texture_file in texture_files:
            texture_key = f"models/model_{model_id}/{texture_file.name}"
            await self.storage.upload_file(texture_file, texture_key)

        self.logger.info("Model %s: Uploaded to %s", model_id, result_url)
        return result_url

    async def _cleanup_workspace(self, job_dir: Path) -> None:
        """Clean up job workspace directory."""
        if job_dir.exists():
            import shutil
            shutil.rmtree(job_dir, ignore_errors=True)
            self.logger.info("Cleaned up workspace: %s", job_dir)



__all__ = ["MeshroomService", "JobStatus"]

