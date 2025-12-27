"""Metrics collection for the orchestrator.

Provides counters, histograms, and gauges for observability.
"""

import logging
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CounterMetric:
    """A monotonically increasing counter."""

    name: str
    value: int = 0
    labels: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def increment(self, amount: int = 1) -> int:
        """Increment the counter.

        Args:
            amount: Amount to add (must be positive)

        Returns:
            New counter value
        """
        if amount < 0:
            raise ValueError("Counter can only be incremented by positive values")
        self.value += amount
        self.updated_at = datetime.now()
        return self.value


@dataclass
class GaugeMetric:
    """A metric that can go up or down."""

    name: str
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def set(self, value: float) -> float:
        """Set the gauge value.

        Args:
            value: New value

        Returns:
            The value that was set
        """
        self.value = value
        self.updated_at = datetime.now()
        return self.value

    def increment(self, amount: float = 1.0) -> float:
        """Increment the gauge.

        Args:
            amount: Amount to add

        Returns:
            New gauge value
        """
        self.value += amount
        self.updated_at = datetime.now()
        return self.value

    def decrement(self, amount: float = 1.0) -> float:
        """Decrement the gauge.

        Args:
            amount: Amount to subtract

        Returns:
            New gauge value
        """
        self.value -= amount
        self.updated_at = datetime.now()
        return self.value


@dataclass
class HistogramMetric:
    """A metric that tracks value distributions."""

    name: str
    values: list[float] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    max_samples: int = 10000

    def observe(self, value: float) -> None:
        """Record a value observation.

        Args:
            value: Value to record
        """
        self.values.append(value)
        if len(self.values) > self.max_samples:
            # Keep the most recent samples
            self.values = self.values[-self.max_samples:]
        self.updated_at = datetime.now()

    def get_stats(self) -> dict[str, float]:
        """Get distribution statistics.

        Returns:
            Dict with count, sum, mean, min, max, p50, p90, p99
        """
        if not self.values:
            return {
                "count": 0,
                "sum": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
            }

        sorted_values = sorted(self.values)
        count = len(sorted_values)

        return {
            "count": count,
            "sum": sum(sorted_values),
            "mean": statistics.mean(sorted_values),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": self._percentile(sorted_values, 50),
            "p90": self._percentile(sorted_values, 90),
            "p99": self._percentile(sorted_values, 99),
        }

    def _percentile(self, sorted_values: list[float], percentile: int) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_values) else f
        if f == c:
            return sorted_values[int(k)]
        return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)


class Timer:
    """Context manager for timing operations."""

    def __init__(self, histogram: HistogramMetric):
        """Initialize timer.

        Args:
            histogram: Histogram to record duration to
        """
        self._histogram = histogram
        self._start_time: float | None = None

    def __enter__(self) -> "Timer":
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        if self._start_time is not None:
            duration_ms = (time.perf_counter() - self._start_time) * 1000
            self._histogram.observe(duration_ms)


class MetricsCollector:
    """Collects and aggregates metrics for the orchestrator.

    Provides counters, gauges, and histograms with optional labels.

    Example:
        collector = MetricsCollector()

        # Counter
        collector.increment("tasks_completed", labels={"agent": "python-developer"})

        # Gauge
        collector.gauge_set("active_agents", 5)

        # Histogram
        collector.histogram("task_duration_ms", 150.5, labels={"agent": "sql-expert"})

        # Timer
        with collector.timer("api_call_duration_ms"):
            await make_api_call()

        # Get summary
        summary = collector.get_summary()
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self._counters: dict[str, CounterMetric] = {}
        self._gauges: dict[str, GaugeMetric] = {}
        self._histograms: dict[str, HistogramMetric] = {}
        self._created_at: datetime = datetime.now()

    def _make_key(self, name: str, labels: dict[str, str] | None = None) -> str:
        """Create a unique key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    # === Counter Operations ===

    def increment(
        self,
        name: str,
        value: int = 1,
        labels: dict[str, str] | None = None,
    ) -> int:
        """Increment a counter.

        Args:
            name: Counter name
            value: Amount to increment by
            labels: Optional labels for the counter

        Returns:
            New counter value
        """
        key = self._make_key(name, labels)
        if key not in self._counters:
            self._counters[key] = CounterMetric(name=name, labels=labels or {})
        return self._counters[key].increment(value)

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> int:
        """Get current counter value.

        Args:
            name: Counter name
            labels: Optional labels

        Returns:
            Current counter value (0 if not exists)
        """
        key = self._make_key(name, labels)
        counter = self._counters.get(key)
        return counter.value if counter else 0

    # === Gauge Operations ===

    def gauge_set(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> float:
        """Set a gauge value.

        Args:
            name: Gauge name
            value: Value to set
            labels: Optional labels

        Returns:
            The value that was set
        """
        key = self._make_key(name, labels)
        if key not in self._gauges:
            self._gauges[key] = GaugeMetric(name=name, labels=labels or {})
        return self._gauges[key].set(value)

    def gauge_increment(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
    ) -> float:
        """Increment a gauge.

        Args:
            name: Gauge name
            value: Amount to increment
            labels: Optional labels

        Returns:
            New gauge value
        """
        key = self._make_key(name, labels)
        if key not in self._gauges:
            self._gauges[key] = GaugeMetric(name=name, labels=labels or {})
        return self._gauges[key].increment(value)

    def gauge_decrement(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
    ) -> float:
        """Decrement a gauge.

        Args:
            name: Gauge name
            value: Amount to decrement
            labels: Optional labels

        Returns:
            New gauge value
        """
        key = self._make_key(name, labels)
        if key not in self._gauges:
            self._gauges[key] = GaugeMetric(name=name, labels=labels or {})
        return self._gauges[key].decrement(value)

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get current gauge value.

        Args:
            name: Gauge name
            labels: Optional labels

        Returns:
            Current gauge value (0.0 if not exists)
        """
        key = self._make_key(name, labels)
        gauge = self._gauges.get(key)
        return gauge.value if gauge else 0.0

    # === Histogram Operations ===

    def histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a histogram observation.

        Args:
            name: Histogram name
            value: Value to observe
            labels: Optional labels
        """
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = HistogramMetric(name=name, labels=labels or {})
        self._histograms[key].observe(value)

    def timer(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> Timer:
        """Create a timer context manager.

        Records duration in milliseconds to the named histogram.

        Args:
            name: Histogram name for timing
            labels: Optional labels

        Returns:
            Timer context manager
        """
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = HistogramMetric(name=name, labels=labels or {})
        return Timer(self._histograms[key])

    def get_histogram_stats(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> dict[str, float]:
        """Get histogram statistics.

        Args:
            name: Histogram name
            labels: Optional labels

        Returns:
            Dict with count, sum, mean, min, max, percentiles
        """
        key = self._make_key(name, labels)
        histogram = self._histograms.get(key)
        if histogram:
            return histogram.get_stats()
        return {
            "count": 0,
            "sum": 0.0,
            "mean": 0.0,
            "min": 0.0,
            "max": 0.0,
            "p50": 0.0,
            "p90": 0.0,
            "p99": 0.0,
        }

    # === Summary Operations ===

    def get_summary(self) -> dict[str, Any]:
        """Get a complete summary of all metrics.

        Returns:
            Dictionary with all counters, gauges, and histograms
        """
        counters = {}
        for key, counter in self._counters.items():
            counters[key] = {
                "value": counter.value,
                "labels": counter.labels,
                "updated_at": counter.updated_at.isoformat(),
            }

        gauges = {}
        for key, gauge in self._gauges.items():
            gauges[key] = {
                "value": gauge.value,
                "labels": gauge.labels,
                "updated_at": gauge.updated_at.isoformat(),
            }

        histograms = {}
        for key, histogram in self._histograms.items():
            stats = histogram.get_stats()
            histograms[key] = {
                "stats": stats,
                "labels": histogram.labels,
                "updated_at": histogram.updated_at.isoformat(),
            }

        return {
            "created_at": self._created_at.isoformat(),
            "counters": counters,
            "gauges": gauges,
            "histograms": histograms,
            "totals": {
                "counter_count": len(self._counters),
                "gauge_count": len(self._gauges),
                "histogram_count": len(self._histograms),
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._created_at = datetime.now()
        logger.info("Metrics collector reset")


# Singleton metrics collector
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the singleton MetricsCollector instance.

    Returns:
        The global MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# Convenience functions for common metrics

def record_task_started(agent_name: str) -> None:
    """Record a task start event."""
    collector = get_metrics_collector()
    collector.increment("tasks_started_total", labels={"agent": agent_name})
    collector.gauge_increment("tasks_in_progress")


def record_task_completed(agent_name: str, duration_ms: float, success: bool) -> None:
    """Record a task completion event."""
    collector = get_metrics_collector()
    status = "success" if success else "failure"
    collector.increment("tasks_completed_total", labels={"agent": agent_name, "status": status})
    collector.histogram("task_duration_ms", duration_ms, labels={"agent": agent_name})
    collector.gauge_decrement("tasks_in_progress")


def record_agent_spawned(agent_name: str) -> None:
    """Record an agent spawn event."""
    collector = get_metrics_collector()
    collector.increment("agents_spawned_total", labels={"agent": agent_name})


def record_api_call(endpoint: str, duration_ms: float, success: bool) -> None:
    """Record an API call."""
    collector = get_metrics_collector()
    status = "success" if success else "error"
    collector.increment("api_calls_total", labels={"endpoint": endpoint, "status": status})
    collector.histogram("api_call_duration_ms", duration_ms, labels={"endpoint": endpoint})
