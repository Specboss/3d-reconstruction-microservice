from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from loguru._logger import Logger

from app.core.params.request_id import RequestId


class TempFileManager:
    """
    Менеджер для работы с временными файлами.
    Управляет созданием, использованием и автоматической очисткой временных файлов.
    """

    def __init__(
        self,
        base_dir: str | Path | None = None,
        logger: Logger | None = None,
        request_id: RequestId | None = None,
    ) -> None:
        """
        Args:
            base_dir: Базовая директория для временных файлов.
                     Если None, используется системная временная директория.
            logger: Логгер для записи операций.
        """
        self.base_dir = Path(base_dir) if base_dir else Path(tempfile.gettempdir())
        self.logger = logger
        self.request_id = request_id
        self._created_files: list[Path] = []
        self._created_dirs: list[Path] = []

    def _log(self, level: str, message: str) -> None:
        if not self.logger:
            return
        formatted = (
            f"{self.request_id.id}: {message}"
            if self.request_id
            else message
        )
        log_method = getattr(self.logger, level, None)
        if log_method:
            log_method(formatted)

    def create_dir(self, *path_parts: str) -> Path:
        """
        Создает временную директорию по указанному пути.

        Args:
            *path_parts: Части пути относительно base_dir.

        Returns:
            Path: Путь к созданной директории.
        """
        dir_path = self.base_dir / Path(*path_parts)
        dir_path.mkdir(parents=True, exist_ok=True)
        self._created_dirs.append(dir_path)
        
        self._log("debug", f"Создана временная директория: {dir_path}")
        
        return dir_path

    def create_file_path(self, *path_parts: str) -> Path:
        """
        Создает путь к временному файлу (не создает сам файл).

        Args:
            *path_parts: Части пути относительно base_dir.

        Returns:
            Path: Путь к файлу.
        """
        file_path = self.base_dir / Path(*path_parts)
        # Создаем родительскую директорию если нужно
        file_path.parent.mkdir(parents=True, exist_ok=True)
        return file_path

    def register_file(self, file_path: str | Path) -> None:
        """
        Регистрирует файл для последующей очистки.

        Args:
            file_path: Путь к файлу для регистрации.
        """
        path = Path(file_path)
        if path not in self._created_files:
            self._created_files.append(path)

    def cleanup_file(self, file_path: str | Path) -> bool:
        """
        Удаляет один файл.

        Args:
            file_path: Путь к файлу для удаления.

        Returns:
            bool: True если файл был удален, False если не существовал или ошибка.
        """
        path = Path(file_path)
        if not path.exists():
            return False

        try:
            path.unlink()
            self._log("debug", f"Удалён временный файл: {path}")
            return True
        except Exception as error:
            self._log("error", f"Не удалось удалить временный файл {path}: {error}")
            return False

    def cleanup_all(self) -> None:
        """Удаляет все зарегистрированные файлы и директории."""
        # Удаляем файлы
        for file_path in self._created_files:
            self.cleanup_file(file_path)
        
        # Удаляем директории (в обратном порядке, чтобы сначала удалить вложенные)
        for dir_path in reversed(self._created_dirs):
            try:
                if dir_path.exists():
                    dir_path.rmdir()
                    self._log("debug", f"Удалена временная директория: {dir_path}")
            except Exception as error:
                self._log(
                    "error",
                    f"Не удалось удалить временную директорию {dir_path}: {error}",
                )

    @contextmanager
    def managed_file(
        self,
        *path_parts: str,
        auto_cleanup: bool = True,
    ) -> Iterator[Path]:
        """
        Context manager для автоматической очистки временного файла.

        Args:
            *path_parts: Части пути к файлу.
            auto_cleanup: Автоматически удалять файл при выходе из контекста.

        Yields:
            Path: Путь к временному файлу.
        """
        file_path = self.create_file_path(*path_parts)
        self.register_file(file_path)
        
        try:
            yield file_path
        finally:
            if auto_cleanup:
                self.cleanup_file(file_path)

    def __enter__(self) -> TempFileManager:
        """Поддержка context manager для автоматической очистки всех файлов."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Автоматическая очистка при выходе из контекста."""
        self.cleanup_all()

