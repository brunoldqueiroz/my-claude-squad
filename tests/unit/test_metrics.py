"""Tests for orchestrator/metrics.py - MetricsCollector."""

import time

import pytest

from orchestrator.metrics import (
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
    MetricsCollector,
    Timer,
    get_metrics_collector,
    record_agent_spawned,
    record_api_call,
    record_task_completed,
    record_task_started,
)


class TestCounterMetric:
    """Tests for CounterMetric."""

    def test_starts_at_zero(self):
        """Counter starts with value 0."""
        counter = CounterMetric(name="test")
        assert counter.value == 0

    def test_increment_by_one(self):
        """Default increment adds 1."""
        counter = CounterMetric(name="test")
        result = counter.increment()
        assert result == 1
        assert counter.value == 1

    def test_increment_by_custom_amount(self):
        """Can increment by custom positive amount."""
        counter = CounterMetric(name="test")
        counter.increment(5)
        assert counter.value == 5

    def test_increment_negative_raises(self):
        """Incrementing by negative value raises ValueError."""
        counter = CounterMetric(name="test")
        with pytest.raises(ValueError, match="positive"):
            counter.increment(-1)

    def test_increment_updates_timestamp(self):
        """Increment updates updated_at timestamp."""
        counter = CounterMetric(name="test")
        old_updated = counter.updated_at
        time.sleep(0.01)
        counter.increment()
        assert counter.updated_at > old_updated


class TestGaugeMetric:
    """Tests for GaugeMetric."""

    def test_starts_at_zero(self):
        """Gauge starts with value 0."""
        gauge = GaugeMetric(name="test")
        assert gauge.value == 0.0

    def test_set_value(self):
        """Can set arbitrary value."""
        gauge = GaugeMetric(name="test")
        result = gauge.set(42.5)
        assert result == 42.5
        assert gauge.value == 42.5

    def test_increment(self):
        """Can increment gauge."""
        gauge = GaugeMetric(name="test")
        gauge.set(10.0)
        result = gauge.increment(5.0)
        assert result == 15.0

    def test_decrement(self):
        """Can decrement gauge."""
        gauge = GaugeMetric(name="test")
        gauge.set(10.0)
        result = gauge.decrement(3.0)
        assert result == 7.0

    def test_can_go_negative(self):
        """Gauge can have negative value."""
        gauge = GaugeMetric(name="test")
        gauge.decrement(5.0)
        assert gauge.value == -5.0


class TestHistogramMetric:
    """Tests for HistogramMetric."""

    def test_observe_adds_value(self):
        """Observe adds value to list."""
        histogram = HistogramMetric(name="test")
        histogram.observe(10.0)
        histogram.observe(20.0)
        assert len(histogram.values) == 2
        assert 10.0 in histogram.values
        assert 20.0 in histogram.values

    def test_get_stats_empty(self):
        """get_stats returns zeros for empty histogram."""
        histogram = HistogramMetric(name="test")
        stats = histogram.get_stats()
        assert stats["count"] == 0
        assert stats["sum"] == 0.0
        assert stats["mean"] == 0.0

    def test_get_stats_with_values(self):
        """get_stats calculates correct statistics."""
        histogram = HistogramMetric(name="test")
        for v in [10.0, 20.0, 30.0, 40.0, 50.0]:
            histogram.observe(v)

        stats = histogram.get_stats()

        assert stats["count"] == 5
        assert stats["sum"] == 150.0
        assert stats["mean"] == 30.0
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0

    def test_percentiles(self):
        """Percentiles are calculated correctly."""
        histogram = HistogramMetric(name="test")
        for v in range(1, 101):  # 1 to 100
            histogram.observe(float(v))

        stats = histogram.get_stats()

        assert stats["p50"] == pytest.approx(50.0, rel=0.1)
        assert stats["p90"] == pytest.approx(90.0, rel=0.1)
        assert stats["p99"] == pytest.approx(99.0, rel=0.1)

    def test_max_samples_limit(self):
        """Histogram limits stored samples to max_samples."""
        histogram = HistogramMetric(name="test", max_samples=10)
        for v in range(100):
            histogram.observe(float(v))

        assert len(histogram.values) == 10
        # Should keep most recent values
        assert histogram.values[-1] == 99.0


class TestTimer:
    """Tests for Timer context manager."""

    def test_timer_records_duration(self):
        """Timer records duration to histogram."""
        histogram = HistogramMetric(name="test")
        timer = Timer(histogram)

        with timer:
            time.sleep(0.01)  # 10ms

        assert len(histogram.values) == 1
        # Duration should be approximately 10ms
        assert histogram.values[0] >= 10.0

    def test_timer_returns_self(self):
        """Timer __enter__ returns self."""
        histogram = HistogramMetric(name="test")
        timer = Timer(histogram)

        with timer as t:
            assert t is timer


class TestMetricsCollectorCounters:
    """Tests for MetricsCollector counter operations."""

    def test_increment_creates_counter(self, metrics):
        """Increment creates counter if not exists."""
        metrics.increment("new_counter")
        assert metrics.get_counter("new_counter") == 1

    def test_increment_multiple_times(self, metrics):
        """Counter accumulates across increments."""
        metrics.increment("counter")
        metrics.increment("counter")
        metrics.increment("counter", value=5)
        assert metrics.get_counter("counter") == 7

    def test_counter_with_labels(self, metrics):
        """Counters with different labels are separate."""
        metrics.increment("requests", labels={"endpoint": "/api/v1"})
        metrics.increment("requests", labels={"endpoint": "/api/v2"})
        metrics.increment("requests", labels={"endpoint": "/api/v1"})

        assert metrics.get_counter("requests", labels={"endpoint": "/api/v1"}) == 2
        assert metrics.get_counter("requests", labels={"endpoint": "/api/v2"}) == 1

    def test_get_counter_nonexistent(self, metrics):
        """Getting nonexistent counter returns 0."""
        assert metrics.get_counter("nonexistent") == 0


class TestMetricsCollectorGauges:
    """Tests for MetricsCollector gauge operations."""

    def test_gauge_set(self, metrics):
        """Can set gauge value."""
        metrics.gauge_set("active_connections", 42.0)
        assert metrics.get_gauge("active_connections") == 42.0

    def test_gauge_increment(self, metrics):
        """Can increment gauge."""
        metrics.gauge_set("workers", 5.0)
        metrics.gauge_increment("workers", 2.0)
        assert metrics.get_gauge("workers") == 7.0

    def test_gauge_decrement(self, metrics):
        """Can decrement gauge."""
        metrics.gauge_set("queue_size", 10.0)
        metrics.gauge_decrement("queue_size", 3.0)
        assert metrics.get_gauge("queue_size") == 7.0

    def test_gauge_with_labels(self, metrics):
        """Gauges with different labels are separate."""
        metrics.gauge_set("memory", 100.0, labels={"host": "a"})
        metrics.gauge_set("memory", 200.0, labels={"host": "b"})

        assert metrics.get_gauge("memory", labels={"host": "a"}) == 100.0
        assert metrics.get_gauge("memory", labels={"host": "b"}) == 200.0

    def test_get_gauge_nonexistent(self, metrics):
        """Getting nonexistent gauge returns 0.0."""
        assert metrics.get_gauge("nonexistent") == 0.0


class TestMetricsCollectorHistograms:
    """Tests for MetricsCollector histogram operations."""

    def test_histogram_observe(self, metrics):
        """Can record histogram observations."""
        metrics.histogram("latency", 10.0)
        metrics.histogram("latency", 20.0)
        metrics.histogram("latency", 30.0)

        stats = metrics.get_histogram_stats("latency")
        assert stats["count"] == 3
        assert stats["mean"] == 20.0

    def test_histogram_with_labels(self, metrics):
        """Histograms with different labels are separate."""
        metrics.histogram("duration", 100.0, labels={"op": "read"})
        metrics.histogram("duration", 200.0, labels={"op": "write"})

        read_stats = metrics.get_histogram_stats("duration", labels={"op": "read"})
        write_stats = metrics.get_histogram_stats("duration", labels={"op": "write"})

        assert read_stats["count"] == 1
        assert read_stats["mean"] == 100.0
        assert write_stats["count"] == 1
        assert write_stats["mean"] == 200.0

    def test_get_histogram_stats_nonexistent(self, metrics):
        """Getting nonexistent histogram returns zeros."""
        stats = metrics.get_histogram_stats("nonexistent")
        assert stats["count"] == 0
        assert stats["sum"] == 0.0


class TestMetricsCollectorTimer:
    """Tests for MetricsCollector timer."""

    def test_timer_creates_histogram(self, metrics):
        """Timer creates histogram if not exists."""
        with metrics.timer("operation_time"):
            time.sleep(0.01)

        stats = metrics.get_histogram_stats("operation_time")
        assert stats["count"] == 1
        assert stats["mean"] >= 10.0  # At least 10ms

    def test_timer_with_labels(self, metrics):
        """Timer respects labels."""
        with metrics.timer("api_duration", labels={"endpoint": "/test"}):
            time.sleep(0.01)

        stats = metrics.get_histogram_stats("api_duration", labels={"endpoint": "/test"})
        assert stats["count"] == 1


class TestMetricsCollectorSummary:
    """Tests for MetricsCollector summary."""

    def test_get_summary_structure(self, metrics):
        """get_summary returns expected structure."""
        metrics.increment("counter1")
        metrics.gauge_set("gauge1", 5.0)
        metrics.histogram("hist1", 10.0)

        summary = metrics.get_summary()

        assert "created_at" in summary
        assert "counters" in summary
        assert "gauges" in summary
        assert "histograms" in summary
        assert "totals" in summary

    def test_get_summary_totals(self, metrics):
        """get_summary has correct totals."""
        metrics.increment("c1")
        metrics.increment("c2")
        metrics.gauge_set("g1", 1.0)
        metrics.histogram("h1", 1.0)
        metrics.histogram("h2", 2.0)

        summary = metrics.get_summary()

        assert summary["totals"]["counter_count"] == 2
        assert summary["totals"]["gauge_count"] == 1
        assert summary["totals"]["histogram_count"] == 2


class TestMetricsCollectorReset:
    """Tests for MetricsCollector reset."""

    def test_reset_clears_all(self, metrics):
        """reset() clears all metrics."""
        metrics.increment("counter")
        metrics.gauge_set("gauge", 10.0)
        metrics.histogram("hist", 5.0)

        metrics.reset()

        assert metrics.get_counter("counter") == 0
        assert metrics.get_gauge("gauge") == 0.0
        assert metrics.get_histogram_stats("hist")["count"] == 0


class TestMetricsCollectorSingleton:
    """Tests for singleton behavior."""

    def test_get_metrics_collector_singleton(self):
        """get_metrics_collector returns same instance."""
        import orchestrator.metrics

        orchestrator.metrics._metrics_collector = None

        m1 = get_metrics_collector()
        m2 = get_metrics_collector()

        assert m1 is m2


class TestConvenienceFunctions:
    """Tests for convenience helper functions."""

    def test_record_task_started(self):
        """record_task_started increments counter and gauge."""
        import orchestrator.metrics

        orchestrator.metrics._metrics_collector = None
        collector = get_metrics_collector()
        collector.reset()

        record_task_started("test-agent")

        assert collector.get_counter("tasks_started_total", labels={"agent": "test-agent"}) == 1
        assert collector.get_gauge("tasks_in_progress") == 1.0

    def test_record_task_completed_success(self):
        """record_task_completed with success."""
        import orchestrator.metrics

        orchestrator.metrics._metrics_collector = None
        collector = get_metrics_collector()
        collector.reset()
        collector.gauge_set("tasks_in_progress", 1.0)

        record_task_completed("test-agent", duration_ms=150.0, success=True)

        assert collector.get_counter("tasks_completed_total", labels={"agent": "test-agent", "status": "success"}) == 1
        assert collector.get_gauge("tasks_in_progress") == 0.0

    def test_record_task_completed_failure(self):
        """record_task_completed with failure."""
        import orchestrator.metrics

        orchestrator.metrics._metrics_collector = None
        collector = get_metrics_collector()
        collector.reset()

        record_task_completed("test-agent", duration_ms=50.0, success=False)

        assert collector.get_counter("tasks_completed_total", labels={"agent": "test-agent", "status": "failure"}) == 1

    def test_record_agent_spawned(self):
        """record_agent_spawned increments counter."""
        import orchestrator.metrics

        orchestrator.metrics._metrics_collector = None
        collector = get_metrics_collector()
        collector.reset()

        record_agent_spawned("python-developer")

        assert collector.get_counter("agents_spawned_total", labels={"agent": "python-developer"}) == 1

    def test_record_api_call(self):
        """record_api_call records counter and histogram."""
        import orchestrator.metrics

        orchestrator.metrics._metrics_collector = None
        collector = get_metrics_collector()
        collector.reset()

        record_api_call("/api/v1/task", duration_ms=100.0, success=True)
        record_api_call("/api/v1/task", duration_ms=50.0, success=False)

        assert collector.get_counter("api_calls_total", labels={"endpoint": "/api/v1/task", "status": "success"}) == 1
        assert collector.get_counter("api_calls_total", labels={"endpoint": "/api/v1/task", "status": "error"}) == 1
