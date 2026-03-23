"""Prometheus-style metrics monitoring module.

Provides metrics collection and exposition for monitoring API performance.
"""
import time
from typing import Callable, Optional, Dict, Any
from functools import wraps
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from loguru import logger


class MetricCollector:
    """Simple Prometheus-style metric collector without external dependencies."""
    
    def __init__(self):
        """Initialize metric collector."""
        self._counters: Dict[str, Dict[tuple, float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: Dict[str, Dict[tuple, list]] = defaultdict(lambda: defaultdict(list))
        self._gauges: Dict[str, Dict[tuple, float]] = defaultdict(lambda: defaultdict(float))
        self._labels: Dict[str, list] = {}
    
    def counter(self, name: str, description: str = "", labels: Optional[list] = None) -> "Counter":
        """Create or get a counter metric.
        
        Args:
            name: Metric name.
            description: Metric description.
            labels: List of label names.
            
        Returns:
            Counter metric instance.
        """
        self._labels[name] = labels or []
        return Counter(self, name, description, labels or [])
    
    def histogram(self, name: str, description: str = "", labels: Optional[list] = None, 
                  buckets: Optional[list] = None) -> "Histogram":
        """Create or get a histogram metric.
        
        Args:
            name: Metric name.
            description: Metric description.
            labels: List of label names.
            buckets: Histogram bucket boundaries.
            
        Returns:
            Histogram metric instance.
        """
        self._labels[name] = labels or []
        return Histogram(self, name, description, labels or [], buckets)
    
    def gauge(self, name: str, description: str = "", labels: Optional[list] = None) -> "Gauge":
        """Create or get a gauge metric.
        
        Args:
            name: Metric name.
            description: Metric description.
            labels: List of label names.
            
        Returns:
            Gauge metric instance.
        """
        self._labels[name] = labels or []
        return Gauge(self, name, description, labels or [])
    
    def _increment_counter(self, name: str, labels: tuple, value: float = 1.0) -> None:
        """Increment counter value."""
        self._counters[name][labels] += value
    
    def _observe_histogram(self, name: str, labels: tuple, value: float) -> None:
        """Observe histogram value."""
        self._histograms[name][labels].append(value)
    
    def _set_gauge(self, name: str, labels: tuple, value: float) -> None:
        """Set gauge value."""
        self._gauges[name][labels] = value
    
    def _get_counter_value(self, name: str, labels: tuple) -> float:
        """Get counter value."""
        return self._counters[name].get(labels, 0.0)
    
    def _get_histogram_values(self, name: str, labels: tuple) -> list:
        """Get histogram values."""
        return self._histograms[name].get(labels, [])
    
    def _get_gauge_value(self, name: str, labels: tuple) -> float:
        """Get gauge value."""
        return self._gauges[name].get(labels, 0.0)
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format.
        
        Returns:
            Prometheus formatted metrics string.
        """
        lines = []
        
        # Export counters
        for name, label_names in self._labels.items():
            if name in self._counters:
                lines.append(f"# TYPE {name} counter")
                lines.append(f"# HELP {name} {name} counter")
                for labels, value in self._counters[name].items():
                    if labels:
                        label_str = ",".join(f'{k}="{v}"' for k, v in zip(label_names, labels))
                        lines.append(f'{name}{{{label_str}}} {value}')
                    else:
                        lines.append(f'{name} {value}')
                lines.append("")
        
        # Export histograms
        for name, label_names in self._labels.items():
            if name in self._histograms:
                lines.append(f"# TYPE {name} histogram")
                lines.append(f"# HELP {name} {name} histogram")
                
                # Default buckets
                buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
                
                for labels, values in self._histograms[name].items():
                    if not values:
                        continue
                    
                    # Calculate histogram buckets
                    sorted_values = sorted(values)
                    total = len(sorted_values)
                    
                    for bucket in buckets:
                        count = sum(1 for v in sorted_values if v <= bucket)
                        if labels:
                            label_str = ",".join(f'{k}="{v}"' for k, v in zip(label_names, labels))
                            label_str += f',le="{bucket}"'
                            lines.append(f'{name}_bucket{{{label_str}}} {count}')
                        else:
                            lines.append(f'{name}_bucket{{le="{bucket}"}} {count}')
                    
                    # +Inf bucket
                    if labels:
                        label_str = ",".join(f'{k}="{v}"' for k, v in zip(label_names, labels))
                        label_str += ',le="+Inf"'
                        lines.append(f'{name}_bucket{{{label_str}}} {total}')
                    else:
                        lines.append(f'{name}_bucket{{le="+Inf"}} {total}')
                    
                    # Sum and count
                    value_sum = sum(values)
                    if labels:
                        label_str = ",".join(f'{k}="{v}"' for k, v in zip(label_names, labels))
                        lines.append(f'{name}_sum{{{label_str}}} {value_sum:.6f}')
                        lines.append(f'{name}_count{{{label_str}}} {total}')
                    else:
                        lines.append(f'{name}_sum {value_sum:.6f}')
                        lines.append(f'{name}_count {total}')
                lines.append("")
        
        # Export gauges
        for name, label_names in self._labels.items():
            if name in self._gauges:
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"# HELP {name} {name} gauge")
                for labels, value in self._gauges[name].items():
                    if labels:
                        label_str = ",".join(f'{k}="{v}"' for k, v in zip(label_names, labels))
                        lines.append(f'{name}{{{label_str}}} {value}')
                    else:
                        lines.append(f'{name} {value}')
                lines.append("")
        
        return "\n".join(lines)


class Counter:
    """Counter metric type."""
    
    def __init__(self, collector: MetricCollector, name: str, description: str, labels: list):
        """Initialize counter.
        
        Args:
            collector: Metric collector instance.
            name: Metric name.
            description: Metric description.
            labels: List of label names.
        """
        self._collector = collector
        self._name = name
        self._description = description
        self._labels = labels
    
    def labels(self, **kwargs) -> "LabeledCounter":
        """Get labeled counter instance.
        
        Args:
            **kwargs: Label key-value pairs.
            
        Returns:
            Labeled counter instance.
        """
        label_values = tuple(kwargs.get(label, "") for label in self._labels)
        return LabeledCounter(self._collector, self._name, label_values)
    
    def inc(self, value: float = 1.0) -> None:
        """Increment counter by value.
        
        Args:
            value: Value to increment by.
        """
        self._collector._increment_counter(self._name, (), value)


class LabeledCounter:
    """Labeled counter instance."""
    
    def __init__(self, collector: MetricCollector, name: str, labels: tuple):
        """Initialize labeled counter.
        
        Args:
            collector: Metric collector instance.
            name: Metric name.
            labels: Label values tuple.
        """
        self._collector = collector
        self._name = name
        self._labels = labels
    
    def inc(self, value: float = 1.0) -> None:
        """Increment counter by value.
        
        Args:
            value: Value to increment by.
        """
        self._collector._increment_counter(self._name, self._labels, value)


class Histogram:
    """Histogram metric type."""
    
    def __init__(self, collector: MetricCollector, name: str, description: str, 
                 labels: list, buckets: Optional[list] = None):
        """Initialize histogram.
        
        Args:
            collector: Metric collector instance.
            name: Metric name.
            description: Metric description.
            labels: List of label names.
            buckets: Histogram bucket boundaries.
        """
        self._collector = collector
        self._name = name
        self._description = description
        self._labels = labels
        self._buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    
    def labels(self, **kwargs) -> "LabeledHistogram":
        """Get labeled histogram instance.
        
        Args:
            **kwargs: Label key-value pairs.
            
        Returns:
            Labeled histogram instance.
        """
        label_values = tuple(kwargs.get(label, "") for label in self._labels)
        return LabeledHistogram(self._collector, self._name, label_values)
    
    def observe(self, value: float) -> None:
        """Observe a value.
        
        Args:
            value: Value to observe.
        """
        self._collector._observe_histogram(self._name, (), value)


class LabeledHistogram:
    """Labeled histogram instance."""
    
    def __init__(self, collector: MetricCollector, name: str, labels: tuple):
        """Initialize labeled histogram.
        
        Args:
            collector: Metric collector instance.
            name: Metric name.
            labels: Label values tuple.
        """
        self._collector = collector
        self._name = name
        self._labels = labels
    
    def observe(self, value: float) -> None:
        """Observe a value.
        
        Args:
            value: Value to observe.
        """
        self._collector._observe_histogram(self._name, self._labels, value)


class Gauge:
    """Gauge metric type."""
    
    def __init__(self, collector: MetricCollector, name: str, description: str, labels: list):
        """Initialize gauge.
        
        Args:
            collector: Metric collector instance.
            name: Metric name.
            description: Metric description.
            labels: List of label names.
        """
        self._collector = collector
        self._name = name
        self._description = description
        self._labels = labels
    
    def labels(self, **kwargs) -> "LabeledGauge":
        """Get labeled gauge instance.
        
        Args:
            **kwargs: Label key-value pairs.
            
        Returns:
            Labeled gauge instance.
        """
        label_values = tuple(kwargs.get(label, "") for label in self._labels)
        return LabeledGauge(self._collector, self._name, label_values)
    
    def set(self, value: float) -> None:
        """Set gauge value.
        
        Args:
            value: Value to set.
        """
        self._collector._set_gauge(self._name, (), value)


class LabeledGauge:
    """Labeled gauge instance."""
    
    def __init__(self, collector: MetricCollector, name: str, labels: tuple):
        """Initialize labeled gauge.
        
        Args:
            collector: Metric collector instance.
            name: Metric name.
            labels: Label values tuple.
        """
        self._collector = collector
        self._name = name
        self._labels = labels
    
    def set(self, value: float) -> None:
        """Set gauge value.
        
        Args:
            value: Value to set.
        """
        self._collector._set_gauge(self._name, self._labels, value)
    
    def inc(self, value: float = 1.0) -> None:
        """Increment gauge by value.
        
        Args:
            value: Value to increment by.
        """
        current = self._collector._get_gauge_value(self._name, self._labels)
        self._collector._set_gauge(self._name, self._labels, current + value)
    
    def dec(self, value: float = 1.0) -> None:
        """Decrement gauge by value.
        
        Args:
            value: Value to decrement by.
        """
        current = self._collector._get_gauge_value(self._name, self._labels)
        self._collector._set_gauge(self._name, self._labels, current - value)


# Global metric collector instance
metrics = MetricCollector()

# Pre-defined metrics
REQUEST_COUNT = metrics.counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = metrics.histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = metrics.gauge(
    'http_active_requests',
    'Number of active HTTP requests',
    ['method']
)

WEBSOCKET_CONNECTIONS = metrics.gauge(
    'websocket_connections',
    'Number of active WebSocket connections',
    ['cookie_id']
)

MESSAGE_PROCESSED = metrics.counter(
    'messages_processed_total',
    'Total messages processed',
    ['cookie_id', 'message_type']
)

KEYWORD_MATCHES = metrics.counter(
    'keyword_matches_total',
    'Total keyword matches',
    ['cookie_id', 'keyword']
)

AI_REPLY_REQUESTS = metrics.counter(
    'ai_reply_requests_total',
    'Total AI reply requests',
    ['cookie_id', 'model']
)

AI_REPLY_LATENCY = metrics.histogram(
    'ai_reply_duration_seconds',
    'AI reply latency',
    ['cookie_id', 'model']
)

DATABASE_QUERIES = metrics.counter(
    'database_queries_total',
    'Total database queries',
    ['operation', 'table']
)

DATABASE_LATENCY = metrics.histogram(
    'database_query_duration_seconds',
    'Database query latency',
    ['operation', 'table']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting HTTP request metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics.
        
        Args:
            request: HTTP request.
            call_next: Next middleware or handler.
            
        Returns:
            HTTP response.
        """
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Track active requests
        method = request.method
        ACTIVE_REQUESTS.labels(method=method).inc()
        
        # Track request latency
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            endpoint = self._get_endpoint_pattern(request.url.path)
            status = response.status_code
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            endpoint = self._get_endpoint_pattern(request.url.path)
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status="500"
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            raise
            
        finally:
            ACTIVE_REQUESTS.labels(method=method).dec()
    
    def _get_endpoint_pattern(self, path: str) -> str:
        """Get endpoint pattern for metrics grouping.
        
        Args:
            path: Request path.
            
        Returns:
            Endpoint pattern.
        """
        # Group dynamic paths
        parts = path.split("/")
        pattern_parts = []
        
        for part in parts:
            if part.isdigit() or (part and part[0].isdigit()):
                pattern_parts.append("{id}")
            elif len(part) == 8 and all(c in "0123456789abcdef" for c in part.lower()):
                # Likely a UUID or trace_id
                pattern_parts.append("{id}")
            else:
                pattern_parts.append(part)
        
        return "/".join(pattern_parts)


def setup_metrics(app) -> None:
    """Setup metrics middleware and endpoint.
    
    Args:
        app: FastAPI application instance.
    """
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    @app.get("/metrics")
    async def metrics_endpoint():
        """Prometheus metrics endpoint."""
        return Response(
            content=metrics.export_prometheus(),
            media_type="text/plain; charset=utf-8"
        )
    
    logger.info("Metrics middleware and /metrics endpoint configured")


def track_database_query(operation: str, table: str):
    """Decorator to track database query metrics.
    
    Args:
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE).
        table: Database table name.
        
    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                DATABASE_QUERIES.labels(operation=operation, table=table).inc()
                DATABASE_LATENCY.labels(operation=operation, table=table).observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                DATABASE_QUERIES.labels(operation=operation, table=table).inc()
                DATABASE_LATENCY.labels(operation=operation, table=table).observe(duration)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


__all__ = [
    "metrics",
    "MetricCollector",
    "Counter",
    "Histogram",
    "Gauge",
    "MetricsMiddleware",
    "setup_metrics",
    "track_database_query",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "ACTIVE_REQUESTS",
    "WEBSOCKET_CONNECTIONS",
    "MESSAGE_PROCESSED",
    "KEYWORD_MATCHES",
    "AI_REPLY_REQUESTS",
    "AI_REPLY_LATENCY",
    "DATABASE_QUERIES",
    "DATABASE_LATENCY",
]
