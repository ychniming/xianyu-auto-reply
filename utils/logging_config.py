"""Structured logging configuration with trace_id support.

Provides JSON formatted logging with distributed tracing capabilities.
"""
import json
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Optional, Dict, Any
from pathlib import Path

from loguru import logger

# Context variable for trace_id across async boundaries
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_trace_id() -> str:
    """Get current trace_id from context."""
    return trace_id_var.get()


def set_trace_id(trace_id: Optional[str] = None) -> str:
    """Set trace_id in context and return it.
    
    Args:
        trace_id: Optional trace_id to set. If None, generates a new one.
        
    Returns:
        The trace_id that was set.
    """
    tid = trace_id or generate_trace_id()
    trace_id_var.set(tid)
    return tid


def get_request_id() -> str:
    """Get current request_id from context."""
    return request_id_var.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set request_id in context and return it.
    
    Args:
        request_id: Optional request_id to set. If None, generates a new one.
        
    Returns:
        The request_id that was set.
    """
    rid = request_id or generate_trace_id()
    request_id_var.set(rid)
    return rid


def generate_trace_id() -> str:
    """Generate a new trace_id."""
    return str(uuid.uuid4())[:8]


def clear_trace_context() -> None:
    """Clear trace context variables."""
    trace_id_var.set("")
    request_id_var.set("")


class JSONSink:
    """Custom sink for JSON formatted logs."""
    
    def __init__(self, output_stream=None):
        """Initialize JSON sink.
        
        Args:
            output_stream: Output stream for logs. Defaults to stdout.
        """
        self.output_stream = output_stream or sys.stdout
    
    def write(self, message) -> None:
        """Write JSON formatted log entry."""
        record = message.record
        
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
            "trace_id": get_trace_id(),
            "request_id": get_request_id(),
        }
        
        # Add extra fields if present
        if record.get("extra"):
            extra = record["extra"]
            # Filter out internal loguru keys
            filtered_extra = {
                k: v for k, v in extra.items()
                if k not in ("trace_id", "request_id")
            }
            if filtered_extra:
                log_entry["extra"] = filtered_extra
        
        # Add exception info if present
        if record.get("exception"):
            log_entry["exception"] = {
                "type": record["exception"].type.__name__ if record["exception"].type else None,
                "value": str(record["exception"].value) if record["exception"].value else None,
                "traceback": record["exception"].traceback if record["exception"].traceback else None,
            }
        
        self.output_stream.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")
        self.output_stream.flush()


class TextSink:
    """Custom sink for text formatted logs with trace_id."""
    
    def __init__(self, output_stream=None):
        """Initialize text sink.
        
        Args:
            output_stream: Output stream for logs. Defaults to stdout.
        """
        self.output_stream = output_stream or sys.stdout
    
    def write(self, message) -> None:
        """Write text formatted log entry with trace_id."""
        record = message.record
        
        trace_id = get_trace_id()
        request_id = get_request_id()
        
        # Build trace context string
        trace_context = ""
        if trace_id:
            trace_context = f"[trace:{trace_id}]"
        if request_id:
            trace_context += f"[req:{request_id}]"
        
        # Format timestamp
        timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Build log line
        level = record["level"].name
        level_padded = f"{level:<8}"
        
        location = f"{record['module']}:{record['function']}:{record['line']}"
        
        log_line = f"{timestamp} | {level_padded} | {location} | {trace_context} {record['message']}"
        
        # Add exception if present
        if record.get("exception") and record["exception"]:
            log_line += f"\n{record['exception']}"
        
        self.output_stream.write(log_line + "\n")
        self.output_stream.flush()


def setup_logging(
    json_format: bool = False,
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    rotation: str = "1 day",
    retention: str = "7 days",
    compression: str = "zip",
    console_output: bool = True
) -> None:
    """Setup logging configuration.
    
    Args:
        json_format: Whether to use JSON format for logs.
        log_level: Log level (DEBUG, INFO, WARNING, ERROR).
        log_dir: Directory for log files. If None, logs only to console.
        rotation: Log rotation interval.
        retention: Log retention period.
        compression: Log compression format.
        console_output: Whether to output logs to console.
    """
    # Remove default handler
    logger.remove()
    
    # Set log level
    level = log_level.upper()
    
    # Console handler
    if console_output:
        if json_format:
            logger.add(
                JSONSink(),
                level=level,
                format="{message}",
            )
        else:
            logger.add(
                TextSink(),
                level=level,
                format="{message}",
            )
    
    # File handler
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = log_path / "xianyu_{time}.log"
        
        if json_format:
            # JSON file logs
            logger.add(
                JSONSink(),
                level=level,
                format="{message}",
            )
        else:
            # Text file logs with standard format
            format_str = (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            )
            logger.add(
                str(log_file),
                rotation=rotation,
                retention=retention,
                compression=compression,
                level=level,
                format=format_str,
                encoding="utf-8",
            )


def get_logger_with_context(**extra) -> "Logger":
    """Get logger with additional context fields.
    
    Args:
        **extra: Additional context fields to include in logs.
        
    Returns:
        Logger instance with context.
    """
    return logger.bind(**extra)


class TraceContext:
    """Context manager for trace_id handling."""
    
    def __init__(self, trace_id: Optional[str] = None):
        """Initialize trace context.
        
        Args:
            trace_id: Optional trace_id. If None, generates a new one.
        """
        self.trace_id = trace_id or generate_trace_id()
        self._previous_trace_id: Optional[str] = None
        self._previous_request_id: Optional[str] = None
    
    def __enter__(self) -> "TraceContext":
        """Enter trace context."""
        self._previous_trace_id = get_trace_id()
        self._previous_request_id = get_request_id()
        set_trace_id(self.trace_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit trace context."""
        if self._previous_trace_id:
            trace_id_var.set(self._previous_trace_id)
        else:
            trace_id_var.set("")
        
        if self._previous_request_id:
            request_id_var.set(self._previous_request_id)
        else:
            request_id_var.set("")


def log_with_trace(level: str, message: str, **extra) -> None:
    """Log message with trace context.
    
    Args:
        level: Log level (debug, info, warning, error).
        message: Log message.
        **extra: Additional context fields.
    """
    trace_id = get_trace_id()
    request_id = get_request_id()
    
    context = {
        "trace_id": trace_id,
        "request_id": request_id,
        **extra
    }
    
    bound_logger = logger.bind(**context)
    
    level_method = getattr(bound_logger, level.lower(), bound_logger.info)
    level_method(message)


# Convenience functions
def log_info(message: str, **extra) -> None:
    """Log info message with trace context."""
    log_with_trace("info", message, **extra)


def log_error(message: str, **extra) -> None:
    """Log error message with trace context."""
    log_with_trace("error", message, **extra)


def log_warning(message: str, **extra) -> None:
    """Log warning message with trace context."""
    log_with_trace("warning", message, **extra)


def log_debug(message: str, **extra) -> None:
    """Log debug message with trace context."""
    log_with_trace("debug", message, **extra)


__all__ = [
    "logger",
    "setup_logging",
    "get_trace_id",
    "set_trace_id",
    "get_request_id",
    "set_request_id",
    "generate_trace_id",
    "clear_trace_context",
    "TraceContext",
    "JSONSink",
    "TextSink",
    "get_logger_with_context",
    "log_with_trace",
    "log_info",
    "log_error",
    "log_warning",
    "log_debug",
]
