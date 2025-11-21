"""Centralized logging helpers based on loguru."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from loguru import logger as loguru_logger

from app.core.settings import LoggingConfigModel

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "{extra[module]: <30} | "
    "<cyan>{message}</cyan>"
)


class SupportsLogMethod(Protocol):
    def __call__(self, message: str, *args: Any, **kwargs: Any) -> None: ...


@dataclass
class Logger:
    """Thin wrapper around loguru logger bound to module name."""

    module: str

    def _bind(self) -> Any:
        return loguru_logger.bind(module=self.module)

    def __getattr__(self, item: str) -> Callable[..., Any]:
        bound = self._bind()
        attr = getattr(bound, item)
        if not callable(attr):
            raise AttributeError(item)
        return attr


def configure_logging(config: LoggingConfigModel) -> None:
    """Configure global logging according to the provided config."""
    loguru_logger.remove()
    loguru_logger.add(
        sys.stdout,
        level=config.level.upper(),
        format=LOG_FORMAT,
        backtrace=True,
        diagnose=True,
    )


def get_logger(name: str) -> Logger:
    """Return application logger bound to the provided module name."""
    return Logger(module=name)


__all__ = ["configure_logging", "get_logger", "Logger"]
