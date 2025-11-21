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
        job_id: str,
        image_urls: list[str],
    ) -> tuple[JobStatus, str | None]:
        """
        Process a reconstruction job.

        Args:
            job_id: Unique job identifier
            image_urls: List of image URLs to download

        Returns:
            Tuple of (final_status, result_url_or_error)
        """
        job_dir = self.workspace_root / job_id
        images_dir = job_dir / "images"
        cache_dir = job_dir / "cache"
        output_dir = job_dir / "output"

        try:
            # Create directories
            for directory in (images_dir, cache_dir, output_dir):
                directory.mkdir(parents=True, exist_ok=True)

            # Download images
            self.logger.info("Job %s: Downloading %d images", job_id, len(image_urls))
            await self._download_images(image_urls, images_dir)

            # Run Meshroom
            self.logger.info("Job %s: Starting Meshroom processing", job_id)
            await self._run_meshroom(job_id, images_dir, cache_dir, output_dir)

            # Upload results
            self.logger.info("Job %s: Uploading results", job_id)
            result_url = await self._upload_results(job_id, output_dir)

            self.logger.info("Job %s: Completed successfully", job_id)
            return "completed", result_url

        except Exception as exc:
            self.logger.error("Job %s: Failed with error: %s", job_id, exc, exc_info=True)
            return "failed", str(exc)

        finally:
            # Cleanup workspace
            await self._cleanup_workspace(job_dir)

    async def _download_images(self, image_urls: list[str], target_dir: Path) -> None:
        """Download all images to target directory."""
        tasks = []
        for index, url in enumerate(image_urls, start=1):
            filename = self._filename_from_url(url, index)
            local_path = target_dir / filename
            tasks.append(self.storage.download_url(url, local_path))

        await asyncio.gather(*tasks)
        self.logger.info("Downloaded %d images", len(image_urls))

    async def _run_meshroom(
        self,
        job_id: str,
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

        self.logger.info("Job %s: Running command: %s", job_id, shlex.join(command))

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
            self.logger.debug("Job %s stdout: %s", job_id, stdout.decode())
        if stderr:
            self.logger.warning("Job %s stderr: %s", job_id, stderr.decode())

        if process.returncode != 0:
            raise RuntimeError(
                f"Meshroom process failed with exit code {process.returncode}"
            )

    async def _upload_results(self, job_id: str, output_dir: Path) -> str:
        """Upload reconstruction results to storage."""
        # Find the main output file (e.g., texturedMesh.obj)
        result_files = list(output_dir.rglob("*.obj"))
        
        if not result_files:
            raise FileNotFoundError("No .obj file found in output directory")

        main_file = result_files[0]
        remote_key = f"results/{job_id}/{main_file.name}"
        
        result_url = await self.storage.upload_file(main_file, remote_key)
        
        # Also upload textures if present
        texture_files = list(output_dir.rglob("*.png")) + list(output_dir.rglob("*.jpg"))
        for texture_file in texture_files:
            texture_key = f"results/{job_id}/{texture_file.name}"
            await self.storage.upload_file(texture_file, texture_key)

        return result_url

    async def _cleanup_workspace(self, job_dir: Path) -> None:
        """Clean up job workspace directory."""
        if job_dir.exists():
            import shutil
            shutil.rmtree(job_dir, ignore_errors=True)
            self.logger.info("Cleaned up workspace: %s", job_dir)

    @staticmethod
    def _filename_from_url(url: str, fallback_index: int) -> str:
        """Extract filename from URL or generate fallback."""
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        
        if not filename or filename == "/":
            filename = f"image_{fallback_index:04d}.jpg"
        
        return filename


__all__ = ["MeshroomService", "JobStatus"]

