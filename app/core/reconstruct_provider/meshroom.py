"""Meshroom reconstruction provider implementation."""

from __future__ import annotations

import asyncio
import shlex
import zipfile
from pathlib import Path
from typing import Any

from app.core.logger import get_logger
from app.core.reconstruct_provider.base.provider import BaseReconstructProvider
from app.core.settings import MeshroomConfigModel
from app.core.storage.base.storage import BaseStorage


class MeshroomProvider(BaseReconstructProvider):
    """Meshroom photogrammetry reconstruction provider."""

    def __init__(
        self,
        config: MeshroomConfigModel,
        storage: BaseStorage,
    ) -> None:
        """
        Initialize Meshroom provider.

        Args:
            config: Meshroom configuration
            storage: Storage provider for files
        """
        self.config = config
        self.storage = storage
        self.workspace_root = Path(config.workspace_dir)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(self.__class__.__name__)

    async def reconstruct(
        self,
        model_id: int,
        images_zip_url: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Run 3D reconstruction using Meshroom.

        Args:
            model_id: Unique model identifier
            images_zip_url: URL to ZIP archive with input images
            **kwargs: Additional parameters (ignored for Meshroom)

        Returns:
            Dictionary with reconstruction results:
            {
                "model_url": str,      # URL to resulting 3D model
                "texture_urls": list,  # URLs to texture files
                "stats": dict,         # Reconstruction statistics
            }

        Raises:
            RuntimeError: If reconstruction fails
            FileNotFoundError: If no output files found
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

            # Download and extract images
            self.logger.info(f"Model {model_id}: Downloading ZIP from {images_zip_url}")
            await self.storage.download_url(images_zip_url, zip_path)

            self.logger.info(f"Model {model_id}: Extracting images")
            image_count = await self._extract_zip(zip_path, images_dir)

            # Run Meshroom reconstruction
            self.logger.info(f"Model {model_id}: Starting Meshroom processing ({image_count} images)")
            await self._run_meshroom(model_id, images_dir, cache_dir, output_dir)

            # Upload results
            self.logger.info(f"Model {model_id}: Uploading results")
            result = await self._upload_results(model_id, output_dir)

            self.logger.info(f"Model {model_id}: Reconstruction completed successfully")
            return {
                "model_url": result["model_url"],
                "texture_urls": result["texture_urls"],
                "stats": {
                    "input_images": image_count,
                    "provider": "meshroom",
                },
            }

        finally:
            # Always cleanup workspace
            await self._cleanup_workspace(job_dir)

    async def _extract_zip(self, zip_path: Path, target_dir: Path) -> int:
        """
        Extract ZIP archive to target directory.

        Args:
            zip_path: Path to ZIP file
            target_dir: Target extraction directory

        Returns:
            Number of extracted images
        """
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(target_dir)

        # Count extracted images
        image_extensions = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}
        image_count = sum(
            1
            for f in target_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in image_extensions
        )

        self.logger.info("Extracted %d images from ZIP", image_count)
        
        if image_count < 3:
            raise ValueError(f"Not enough images for reconstruction: {image_count} (minimum 3 required)")
        
        return image_count

    async def _run_meshroom(
        self,
        model_id: int,
        images_dir: Path,
        cache_dir: Path,
        output_dir: Path,
    ) -> None:
        """
        Execute Meshroom binary for reconstruction.

        Args:
            model_id: Model identifier (for logging)
            images_dir: Directory with input images
            cache_dir: Cache directory for intermediate files
            output_dir: Output directory for results
        """
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

        self.logger.info(f"Model {model_id}: Running command: {shlex.join(command)}")

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

        stdout_text = stdout.decode() if stdout else ""
        stderr_text = stderr.decode() if stderr else ""
        
        if stdout_text:
            self.logger.debug(f"Model {model_id} stdout: {stdout_text}")
        if stderr_text:
            self.logger.warning(f"Model {model_id} stderr: {stderr_text}")

        if process.returncode != 0:
            error_msg = f"Meshroom process failed with exit code {process.returncode}"
            if stderr_text:
                error_msg += f"\nStderr: {stderr_text}"
            if stdout_text:
                error_msg += f"\nStdout: {stdout_text}"
            raise RuntimeError(error_msg)

    async def _upload_results(self, model_id: int, output_dir: Path) -> dict[str, Any]:
        """
        Upload reconstruction results to storage.

        Args:
            model_id: Model identifier
            output_dir: Directory with output files

        Returns:
            Dictionary with uploaded file URLs
        """
        # Find the main output file (prefer .gltf/.glb, fallback to .obj)
        gltf_files = list(output_dir.rglob("*.gltf")) + list(output_dir.rglob("*.glb"))
        obj_files = list(output_dir.rglob("*.obj"))

        if gltf_files:
            main_file = gltf_files[0]
            model_ext = main_file.suffix
        elif obj_files:
            main_file = obj_files[0]
            model_ext = main_file.suffix
            self.logger.warning(
                "Model %s: Using OBJ format (GLTF not available)",
                model_id,
            )
        else:
            raise FileNotFoundError("No output model file (.gltf/.glb/.obj) found")

        # Upload main model file
        remote_key = f"models/model_{model_id}/model{model_ext}"
        model_url = await self.storage.upload_file(main_file, remote_key)

        # Upload textures if present
        texture_files = list(output_dir.rglob("*.png")) + list(output_dir.rglob("*.jpg"))
        texture_urls = []
        
        for texture_file in texture_files:
            texture_key = f"models/model_{model_id}/{texture_file.name}"
            texture_url = await self.storage.upload_file(texture_file, texture_key)
            texture_urls.append(texture_url)

        self.logger.info(
            "Model %s: Uploaded model and %d textures",
            model_id,
            len(texture_urls),
        )

        return {
            "model_url": model_url,
            "texture_urls": texture_urls,
        }

    async def _cleanup_workspace(self, job_dir: Path) -> None:
        """
        Clean up job workspace directory.

        Args:
            job_dir: Job workspace directory to remove
        """
        if job_dir.exists():
            import shutil

            shutil.rmtree(job_dir, ignore_errors=True)
            self.logger.info(f"Cleaned up workspace: {job_dir}")


__all__ = ["MeshroomProvider"]
