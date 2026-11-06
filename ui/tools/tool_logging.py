"""
GridForge V2
============

File:
    ui/tools/tool_logging.py

Purpose
-------
Structured logging support for the GridForge UI tool subsystem.

ToolLogging provides a thin, framework-neutral diagnostic boundary for
tool activity. It is intended to consume observations from
``tool_observer.py`` and turn them into structured log records.

Architectural rules
-------------------
- Logging is observational only.
- Logging must not mutate Core state.
- Logging must not execute Commands.
- Logging must not activate/deactivate tools.
- Logging must not own tool lifecycle state.
- Logging must not depend on Qt.
- Logging must not become an event bus.
- Python's standard ``logging`` package is the logging backend.
- ToolObservers remain the source of observations.
- ToolLogging may adapt observations to standard logging records.

This module intentionally separates:
    ToolObserver
        -> observes tool activity

    ToolLogging
        -> records diagnostic information

    ToolManager / ToolDispatcher
        -> owns actual tool orchestration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Optional, Protocol

from .tool_observer import (
    ToolObservation,
    ToolObservationSeverity,
    ToolObservationType,
    ToolObserver,
)


# ============================================================
# LOG LEVEL
# ============================================================


class ToolLogLevel(str, Enum):
    """
    Logging levels exposed by the GridForge tool subsystem.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def numeric(self) -> int:
        """Return the corresponding stdlib logging level."""

        return {
            ToolLogLevel.DEBUG: logging.DEBUG,
            ToolLogLevel.INFO: logging.INFO,
            ToolLogLevel.WARNING: logging.WARNING,
            ToolLogLevel.ERROR: logging.ERROR,
            ToolLogLevel.CRITICAL: logging.CRITICAL,
        }[self]


# ============================================================
# LOG CATEGORY
# ============================================================


class ToolLogCategory(str, Enum):
    """
    Logical categories for tool diagnostics.
    """

    LIFECYCLE = "lifecycle"
    INPUT = "input"
    INTERACTION = "interaction"
    EXECUTION = "execution"
    STATE = "state"
    REQUIREMENTS = "requirements"
    ERROR = "error"
    GENERAL = "general"


# ============================================================
# LOG RECORD
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolLogRecord:
    """
    Immutable structured representation of one tool log entry.
    """

    level: ToolLogLevel

    category: ToolLogCategory

    message: str

    observation_type: Optional[
        ToolObservationType
    ] = None

    tool_id: Optional[str] = None

    tool_name: Optional[str] = None

    event_type: Optional[str] = None

    context_id: Optional[str] = None

    exception_type: Optional[str] = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable diagnostic representation."""

        return {
            "level": self.level.value,
            "category": self.category.value,
            "message": self.message,
            "observation_type": (
                self.observation_type.value
                if self.observation_type is not None
                else None
            ),
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "event_type": self.event_type,
            "context_id": self.context_id,
            "exception_type": self.exception_type,
            "metadata": dict(self.metadata),
        }


# ============================================================
# LOG FORMAT
# ============================================================


class ToolLogFormatter(Protocol):
    """
    Protocol for formatting structured tool log records.
    """

    def format(
        self,
        record: ToolLogRecord,
    ) -> str:
        """Format one tool log record."""
        ...


class DefaultToolLogFormatter:
    """
    Compact deterministic formatter for tool log records.
    """

    def format(
        self,
        record: ToolLogRecord,
    ) -> str:
        parts: list[str] = []

        parts.append(
            f"[{record.category.value}]"
        )

        if record.tool_name:
            parts.append(
                f"tool={record.tool_name}"
            )

        if record.tool_id:
            parts.append(
                f"id={record.tool_id}"
            )

        if record.observation_type:
            parts.append(
                f"event={record.observation_type.value}"
            )

        if record.event_type:
            parts.append(
                f"input={record.event_type}"
            )

        parts.append(
            record.message
        )

        return " ".join(parts)


# ============================================================
# LOG SINK
# ============================================================


class ToolLogSink(Protocol):
    """
    Protocol for destinations receiving structured tool log records.
    """

    def write(
        self,
        record: ToolLogRecord,
    ) -> None:
        """Write one log record."""
        ...


class PythonLoggingSink:
    """
    Adapter from ToolLogRecord to Python's logging subsystem.
    """

    def __init__(
        self,
        logger: logging.Logger,
        *,
        formatter: Optional[
            ToolLogFormatter
        ] = None,
    ) -> None:
        if not isinstance(
            logger,
            logging.Logger,
        ):
            raise TypeError(
                "logger must be logging.Logger."
            )

        self._logger = logger

        self._formatter = (
            formatter
            or DefaultToolLogFormatter()
        )

    @property
    def logger(self) -> logging.Logger:
        """Return the underlying logger."""

        return self._logger

    @property
    def formatter(self) -> ToolLogFormatter:
        """Return the configured formatter."""

        return self._formatter

    def write(
        self,
        record: ToolLogRecord,
    ) -> None:
        """Write a structured record."""

        if not isinstance(
            record,
            ToolLogRecord,
        ):
            raise TypeError(
                "record must be ToolLogRecord."
            )

        message = self._formatter.format(
            record
        )

        self._logger.log(
            record.level.numeric,
            message,
            extra={
                "gridforge_tool_log": record.to_dict()
            },
        )


class NullToolLogSink:
    """
    No-op log sink.

    Useful for tests and applications that do not require tool logs.
    """

    def write(
        self,
        record: ToolLogRecord,
    ) -> None:
        """Discard the record."""

        return None


# ============================================================
# OBSERVATION MAPPER
# ============================================================


class ToolObservationLogMapper:
    """
    Maps ToolObservation objects to ToolLogRecord objects.

    Mapping is deterministic and contains no side effects.
    """

    _CATEGORY_MAP = {
        ToolObservationType.ACTIVATING: (
            ToolLogCategory.LIFECYCLE
        ),
        ToolObservationType.ACTIVATED: (
            ToolLogCategory.LIFECYCLE
        ),
        ToolObservationType.DEACTIVATING: (
            ToolLogCategory.LIFECYCLE
        ),
        ToolObservationType.DEACTIVATED: (
            ToolLogCategory.LIFECYCLE
        ),
        ToolObservationType.SUSPENDING: (
            ToolLogCategory.LIFECYCLE
        ),
        ToolObservationType.SUSPENDED: (
            ToolLogCategory.LIFECYCLE
        ),
        ToolObservationType.RESUMING: (
            ToolLogCategory.LIFECYCLE
        ),
        ToolObservationType.RESUMED: (
            ToolLogCategory.LIFECYCLE
        ),
        ToolObservationType.RESETTING: (
            ToolLogCategory.LIFECYCLE
        ),
        ToolObservationType.RESET: (
            ToolLogCategory.LIFECYCLE
        ),
        ToolObservationType.CANCELLING: (
            ToolLogCategory.INTERACTION
        ),
        ToolObservationType.CANCELLED: (
            ToolLogCategory.INTERACTION
        ),
        ToolObservationType.EVENT_RECEIVED: (
            ToolLogCategory.INPUT
        ),
        ToolObservationType.EVENT_HANDLED: (
            ToolLogCategory.INTERACTION
        ),
        ToolObservationType.EVENT_IGNORED: (
            ToolLogCategory.INPUT
        ),
        ToolObservationType.EXECUTION_STARTED: (
            ToolLogCategory.EXECUTION
        ),
        ToolObservationType.EXECUTION_COMPLETED: (
            ToolLogCategory.EXECUTION
        ),
        ToolObservationType.STATE_CHANGED: (
            ToolLogCategory.STATE
        ),
        ToolObservationType.REQUIREMENTS_CHANGED: (
            ToolLogCategory.REQUIREMENTS
        ),
        ToolObservationType.ERROR: (
            ToolLogCategory.ERROR
        ),
    }

    def map(
        self,
        observation: ToolObservation,
    ) -> ToolLogRecord:
        """Convert an observation into a structured log record."""

        if not isinstance(
            observation,
            ToolObservation,
        ):
            raise TypeError(
                "observation must be ToolObservation."
            )

        category = self._CATEGORY_MAP.get(
            observation.observation_type,
            ToolLogCategory.GENERAL,
        )

        level = self._level_for(
            observation
        )

        tool_id, tool_name = (
            self._tool_identity(
                observation.tool
            )
        )

        event_type = self._event_type(
            observation.event
        )

        context_id = self._context_identity(
            observation.context
        )

        exception_type = (
            type(
                observation.error
            ).__name__
            if observation.error is not None
            else None
        )

        message = (
            observation.message.strip()
            if observation.message
            else observation.observation_type.value
        )

        metadata = dict(
            observation.metadata
        )

        metadata.setdefault(
            "observation_type",
            observation.observation_type.value,
        )

        return ToolLogRecord(
            level=level,
            category=category,
            message=message,
            observation_type=(
                observation.observation_type
            ),
            tool_id=tool_id,
            tool_name=tool_name,
            event_type=event_type,
            context_id=context_id,
            exception_type=exception_type,
            metadata=metadata,
        )

    @staticmethod
    def _level_for(
        observation: ToolObservation,
    ) -> ToolLogLevel:
        if observation.error is not None:
            return ToolLogLevel.ERROR

        severity_map = {
            ToolObservationSeverity.DEBUG: (
                ToolLogLevel.DEBUG
            ),
            ToolObservationSeverity.INFO: (
                ToolLogLevel.INFO
            ),
            ToolObservationSeverity.WARNING: (
                ToolLogLevel.WARNING
            ),
            ToolObservationSeverity.ERROR: (
                ToolLogLevel.ERROR
            ),
        }

        return severity_map.get(
            observation.severity,
            ToolLogLevel.INFO,
        )

    @staticmethod
    def _tool_identity(
        tool: Any,
    ) -> tuple[
        Optional[str],
        Optional[str],
    ]:
        if tool is None:
            return None, None

        tool_id = getattr(
            tool,
            "tool_id",
            None,
        )

        if tool_id is None:
            tool_id = getattr(
                tool,
                "id",
                None,
            )

        tool_name = getattr(
            tool,
            "name",
            None,
        )

        if tool_name is None:
            tool_name = tool.__class__.__name__

        return (
            str(tool_id)
            if tool_id is not None
            else None,
            str(tool_name)
            if tool_name is not None
            else None,
        )

    @staticmethod
    def _event_type(
        event: Any,
    ) -> Optional[str]:
        if event is None:
            return None

        event_type = getattr(
            event,
            "event_type",
            None,
        )

        if event_type is None:
            event_type = getattr(
                event,
                "type",
                None,
            )

        if event_type is None:
            event_type = event.__class__.__name__

        return str(
            event_type
        )

    @staticmethod
    def _context_identity(
        context: Any,
    ) -> Optional[str]:
        if context is None:
            return None

        context_id = getattr(
            context,
            "context_id",
            None,
        )

        if context_id is None:
            context_id = getattr(
                context,
                "id",
                None,
            )

        if context_id is None:
            return None

        return str(
            context_id
        )


# ============================================================
# TOOL LOGGER
# ============================================================


class ToolLogger:
    """
    Structured logger for GridForge tool activity.

    ToolLogger can be used directly or registered as a ToolObserver.
    """

    def __init__(
        self,
        sink: Optional[
            ToolLogSink
        ] = None,
        *,
        mapper: Optional[
            ToolObservationLogMapper
        ] = None,
    ) -> None:
        self._sink = (
            sink
            or NullToolLogSink()
        )

        self._mapper = (
            mapper
            or ToolObservationLogMapper()
        )

    @property
    def sink(self) -> ToolLogSink:
        """Return the configured log sink."""

        return self._sink

    @property
    def mapper(self) -> ToolObservationLogMapper:
        """Return the observation mapper."""

        return self._mapper

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """
        Observe and log one ToolObservation.

        This method satisfies the ToolObserver protocol.
        """

        record = self._mapper.map(
            observation
        )

        self.log(
            record
        )

    def log(
        self,
        record: ToolLogRecord,
    ) -> None:
        """Write a structured log record."""

        if not isinstance(
            record,
            ToolLogRecord,
        ):
            raise TypeError(
                "record must be ToolLogRecord."
            )

        self._sink.write(
            record
        )

    def debug(
        self,
        message: str,
        *,
        category: ToolLogCategory = (
            ToolLogCategory.GENERAL
        ),
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:
        """Write a DEBUG record."""

        self.log(
            ToolLogRecord(
                level=ToolLogLevel.DEBUG,
                category=category,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def info(
        self,
        message: str,
        *,
        category: ToolLogCategory = (
            ToolLogCategory.GENERAL
        ),
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:
        """Write an INFO record."""

        self.log(
            ToolLogRecord(
                level=ToolLogLevel.INFO,
                category=category,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def warning(
        self,
        message: str,
        *,
        category: ToolLogCategory = (
            ToolLogCategory.GENERAL
        ),
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:
        """Write a WARNING record."""

        self.log(
            ToolLogRecord(
                level=ToolLogLevel.WARNING,
                category=category,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def error(
        self,
        message: str,
        *,
        category: ToolLogCategory = (
            ToolLogCategory.ERROR
        ),
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:
        """Write an ERROR record."""

        self.log(
            ToolLogRecord(
                level=ToolLogLevel.ERROR,
                category=category,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def critical(
        self,
        message: str,
        *,
        category: ToolLogCategory = (
            ToolLogCategory.ERROR
        ),
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:
        """Write a CRITICAL record."""

        self.log(
            ToolLogRecord(
                level=ToolLogLevel.CRITICAL,
                category=category,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )


# ============================================================
# FILTERED LOGGER
# ============================================================


class FilteredToolLogger:
    """
    Observer adapter that forwards only selected observations to a
    ToolLogger.
    """

    def __init__(
        self,
        logger: ToolLogger,
        *,
        observation_types: Iterable[
            ToolObservationType
        ] = (),
        categories: Iterable[
            ToolLogCategory
        ] = (),
        minimum_level: ToolLogLevel = (
            ToolLogLevel.DEBUG
        ),
    ) -> None:
        if not isinstance(
            logger,
            ToolLogger,
        ):
            raise TypeError(
                "logger must be ToolLogger."
            )

        self._logger = logger

        self._observation_types = frozenset(
            observation_types
        )

        self._categories = frozenset(
            categories
        )

        self._minimum_level = (
            minimum_level
        )

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """Log an observation if it passes the filters."""

        record = self._logger.mapper.map(
            observation
        )

        if (
            self._observation_types
            and observation.observation_type
            not in self._observation_types
        ):
            return

        if (
            self._categories
            and record.category
            not in self._categories
        ):
            return

        if (
            record.level.numeric
            < self._minimum_level.numeric
        ):
            return

        self._logger.log(
            record
        )


# ============================================================
# FACTORY HELPERS
# ============================================================


def create_tool_logger(
    logger_name: str = "gridforge.ui.tools",
    *,
    level: int = logging.INFO,
    formatter: Optional[
        ToolLogFormatter
    ] = None,
) -> ToolLogger:
    """
    Create a ToolLogger backed by Python logging.

    No handlers are installed here. Application-level logging
    configuration remains outside the tool subsystem.
    """

    if not isinstance(
        logger_name,
        str,
    ):
        raise TypeError(
            "logger_name must be a string."
        )

    logger = logging.getLogger(
        logger_name
    )

    logger.setLevel(
        level
    )

    return ToolLogger(
        PythonLoggingSink(
            logger,
            formatter=formatter,
        )
    )


def configure_tool_logging(
    *,
    logger_name: str = "gridforge.ui.tools",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure only the logger level.

    Handler ownership remains with the application.
    """

    logger = logging.getLogger(
        logger_name
    )

    logger.setLevel(
        level
    )

    return logger


__all__ = [
    "ToolLogLevel",
    "ToolLogCategory",
    "ToolLogRecord",
    "ToolLogFormatter",
    "DefaultToolLogFormatter",
    "ToolLogSink",
    "PythonLoggingSink",
    "NullToolLogSink",
    "ToolObservationLogMapper",
    "ToolLogger",
    "FilteredToolLogger",
    "create_tool_logger",
    "configure_tool_logging",
]
