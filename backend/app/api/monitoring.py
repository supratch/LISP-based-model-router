#!/usr/bin/env python3
"""
Monitoring Service for AI Workload Routing System
Provides comprehensive monitoring, alerting, and observability features.
"""

import asyncio
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import statistics

import structlog

logger = structlog.get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class MetricType(Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Alert:
    """System alert definition."""
    id: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def resolve(self):
        """Mark alert as resolved."""
        self.resolved = True
        self.resolution_time = datetime.utcnow()


@dataclass
class Metric:
    """System metric data point."""
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class PerformanceThreshold:
    """Performance threshold for alerting."""
    metric_name: str
    threshold_value: float
    operator: str  # ">", "<", ">=", "<=", "=="
    severity: AlertSeverity
    description: str
    enabled: bool = True


class MonitoringService:
    """Comprehensive monitoring service for the routing system."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize monitoring service."""
        self.config = config or {}
        self.running = False
        
        # Storage for metrics and alerts
        self.metrics: Dict[str, List[Metric]] = {}
        self.alerts: List[Alert] = []
        self.active_alerts: Dict[str, Alert] = {}
        
        # Performance thresholds
        self.thresholds: List[PerformanceThreshold] = []
        self._initialize_default_thresholds()
        
        # Monitoring intervals
        self.metric_collection_interval = 10  # seconds
        self.alert_check_interval = 5  # seconds
        self.metric_retention_hours = 24
        
        # Performance counters
        self.performance_counters = {
            "total_queries": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "lisp_routes": 0,
            "dns_routes": 0,
            "model_selections": {},
            "avg_response_time": 0.0,
            "error_rate": 0.0
        }
        
        logger.info("Monitoring service initialized")
    
    def _initialize_default_thresholds(self):
        """Initialize default performance thresholds."""
        self.thresholds = [
            PerformanceThreshold(
                metric_name="cpu_usage_percent",
                threshold_value=80.0,
                operator=">",
                severity=AlertSeverity.WARNING,
                description="High CPU usage detected"
            ),
            PerformanceThreshold(
                metric_name="memory_usage_percent",
                threshold_value=85.0,
                operator=">",
                severity=AlertSeverity.WARNING,
                description="High memory usage detected"
            ),
            PerformanceThreshold(
                metric_name="error_rate",
                threshold_value=5.0,
                operator=">",
                severity=AlertSeverity.CRITICAL,
                description="High error rate detected"
            ),
            PerformanceThreshold(
                metric_name="avg_response_time",
                threshold_value=10.0,
                operator=">",
                severity=AlertSeverity.WARNING,
                description="High average response time detected"
            ),
            PerformanceThreshold(
                metric_name="model_load",
                threshold_value=90.0,
                operator=">",
                severity=AlertSeverity.CRITICAL,
                description="Model overload detected"
            )
        ]
    
    async def start_monitoring(self):
        """Start all monitoring services."""
        try:
            self.running = True
            
            # Start metric collection
            asyncio.create_task(self._metric_collection_loop())
            
            # Start alert checking
            asyncio.create_task(self._alert_check_loop())
            
            # Start metric cleanup
            asyncio.create_task(self._metric_cleanup_loop())
            
            logger.info("Monitoring services started")
            
        except Exception as e:
            logger.error("Failed to start monitoring services", error=str(e))
            raise
    
    async def _metric_collection_loop(self):
        """Continuously collect system and application metrics."""
        while self.running:
            try:
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await asyncio.sleep(self.metric_collection_interval)
                
            except Exception as e:
                logger.error("Error in metric collection loop", error=str(e))
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            import psutil
            
            current_time = datetime.utcnow()
            
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            self.record_metric(Metric(
                name="cpu_usage_percent",
                metric_type=MetricType.GAUGE,
                value=cpu_usage,
                timestamp=current_time,
                unit="percent"
            ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric(Metric(
                name="memory_usage_percent",
                metric_type=MetricType.GAUGE,
                value=memory.percent,
                timestamp=current_time,
                unit="percent"
            ))
            
            self.record_metric(Metric(
                name="memory_available_bytes",
                metric_type=MetricType.GAUGE,
                value=memory.available,
                timestamp=current_time,
                unit="bytes"
            ))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_metric(Metric(
                name="disk_usage_percent",
                metric_type=MetricType.GAUGE,
                value=(disk.used / disk.total) * 100,
                timestamp=current_time,
                unit="percent"
            ))
            
            # Network statistics
            network = psutil.net_io_counters()
            self.record_metric(Metric(
                name="network_bytes_sent",
                metric_type=MetricType.COUNTER,
                value=network.bytes_sent,
                timestamp=current_time,
                unit="bytes"
            ))
            
            self.record_metric(Metric(
                name="network_bytes_received",
                metric_type=MetricType.COUNTER,
                value=network.bytes_recv,
                timestamp=current_time,
                unit="bytes"
            ))
            
        except Exception as e:
            logger.error("Error collecting system metrics", error=str(e))
    
    async def _collect_application_metrics(self):
        """Collect application-specific metrics."""
        try:
            current_time = datetime.utcnow()
            
            # Performance counters
            self.record_metric(Metric(
                name="total_queries",
                metric_type=MetricType.COUNTER,
                value=self.performance_counters["total_queries"],
                timestamp=current_time
            ))
            
            self.record_metric(Metric(
                name="successful_routes",
                metric_type=MetricType.COUNTER,
                value=self.performance_counters["successful_routes"],
                timestamp=current_time
            ))
            
            self.record_metric(Metric(
                name="failed_routes",
                metric_type=MetricType.COUNTER,
                value=self.performance_counters["failed_routes"],
                timestamp=current_time
            ))
            
            # Calculate error rate
            total = self.performance_counters["total_queries"]
            failed = self.performance_counters["failed_routes"]
            error_rate = (failed / total * 100) if total > 0 else 0.0
            
            self.record_metric(Metric(
                name="error_rate",
                metric_type=MetricType.GAUGE,
                value=error_rate,
                timestamp=current_time,
                unit="percent"
            ))
            
            self.record_metric(Metric(
                name="avg_response_time",
                metric_type=MetricType.GAUGE,
                value=self.performance_counters["avg_response_time"],
                timestamp=current_time,
                unit="seconds"
            ))
            
            # Model-specific metrics
            for model_name, count in self.performance_counters["model_selections"].items():
                self.record_metric(Metric(
                    name="model_selections",
                    metric_type=MetricType.COUNTER,
                    value=count,
                    timestamp=current_time,
                    labels={"model": model_name}
                ))
            
        except Exception as e:
            logger.error("Error collecting application metrics", error=str(e))
    
    async def _alert_check_loop(self):
        """Continuously check metrics against thresholds and generate alerts."""
        while self.running:
            try:
                await self._check_thresholds()
                await asyncio.sleep(self.alert_check_interval)
                
            except Exception as e:
                logger.error("Error in alert check loop", error=str(e))
                await asyncio.sleep(5)
    
    async def _check_thresholds(self):
        """Check all metrics against defined thresholds."""
        for threshold in self.thresholds:
            if not threshold.enabled:
                continue
                
            try:
                # Get recent metrics for this threshold
                recent_metrics = self._get_recent_metrics(threshold.metric_name, minutes=5)
                
                if not recent_metrics:
                    continue
                
                # Use the most recent metric value
                latest_metric = recent_metrics[-1]
                current_value = latest_metric.value
                
                # Check threshold condition
                alert_triggered = self._evaluate_threshold_condition(
                    current_value, threshold.threshold_value, threshold.operator
                )
                
                alert_id = f"{threshold.metric_name}_{threshold.operator}_{threshold.threshold_value}"
                
                if alert_triggered:
                    if alert_id not in self.active_alerts:
                        # Create new alert
                        alert = Alert(
                            id=alert_id,
                            severity=threshold.severity,
                            title=f"Threshold exceeded: {threshold.metric_name}",
                            description=f"{threshold.description}. Current value: {current_value}, Threshold: {threshold.threshold_value}",
                            timestamp=datetime.utcnow(),
                            metadata={
                                "metric_name": threshold.metric_name,
                                "current_value": current_value,
                                "threshold_value": threshold.threshold_value,
                                "operator": threshold.operator
                            }
                        )
                        
                        self.active_alerts[alert_id] = alert
                        self.alerts.append(alert)
                        
                        logger.warning("Alert triggered", 
                                     alert_id=alert_id,
                                     severity=threshold.severity.value,
                                     description=alert.description)
                else:
                    # Resolve alert if it exists
                    if alert_id in self.active_alerts:
                        alert = self.active_alerts[alert_id]
                        alert.resolve()
                        del self.active_alerts[alert_id]
                        
                        logger.info("Alert resolved", 
                                   alert_id=alert_id,
                                   resolution_time=alert.resolution_time)
                        
            except Exception as e:
                logger.error("Error checking threshold", 
                           metric=threshold.metric_name, error=str(e))
    
    def _evaluate_threshold_condition(self, current_value: float, threshold_value: float, operator: str) -> bool:
        """Evaluate threshold condition."""
        if operator == ">":
            return current_value > threshold_value
        elif operator == "<":
            return current_value < threshold_value
        elif operator == ">=":
            return current_value >= threshold_value
        elif operator == "<=":
            return current_value <= threshold_value
        elif operator == "==":
            return current_value == threshold_value
        else:
            logger.warning("Unknown threshold operator", operator=operator)
            return False
    
    async def _metric_cleanup_loop(self):
        """Clean up old metrics to prevent memory growth."""
        while self.running:
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error("Error in metric cleanup loop", error=str(e))
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    async def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.metric_retention_hours)
        removed_count = 0
        
        for metric_name, metric_list in self.metrics.items():
            original_count = len(metric_list)
            self.metrics[metric_name] = [
                metric for metric in metric_list 
                if metric.timestamp >= cutoff_time
            ]
            removed_count += original_count - len(self.metrics[metric_name])
        
        if removed_count > 0:
            logger.debug("Old metrics cleaned up", removed_count=removed_count)
    
    def record_metric(self, metric: Metric):
        """Record a new metric data point."""
        if metric.name not in self.metrics:
            self.metrics[metric.name] = []
        
        self.metrics[metric.name].append(metric)
        
        # Keep only recent metrics in memory (last 1000 points)
        if len(self.metrics[metric.name]) > 1000:
            self.metrics[metric.name] = self.metrics[metric.name][-1000:]
    
    def _get_recent_metrics(self, metric_name: str, minutes: int = 10) -> List[Metric]:
        """Get metrics from the last N minutes."""
        if metric_name not in self.metrics:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            metric for metric in self.metrics[metric_name]
            if metric.timestamp >= cutoff_time
        ]
    
    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        metric = Metric(
            name=name,
            metric_type=MetricType.COUNTER,
            value=1,
            timestamp=datetime.utcnow(),
            labels=labels or {}
        )
        self.record_metric(metric)
    
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None, unit: str = ""):
        """Record a gauge metric."""
        metric = Metric(
            name=name,
            metric_type=MetricType.GAUGE,
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            unit=unit
        )
        self.record_metric(metric)
    
    def record_timing(self, name: str, duration_seconds: float, labels: Optional[Dict[str, str]] = None):
        """Record a timing metric."""
        metric = Metric(
            name=name,
            metric_type=MetricType.TIMER,
            value=duration_seconds,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            unit="seconds"
        )
        self.record_metric(metric)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics."""
        summary = {
            "total_metrics": sum(len(metrics) for metrics in self.metrics.values()),
            "metric_types": list(self.metrics.keys()),
            "collection_period_hours": self.metric_retention_hours,
            "recent_metrics": {}
        }
        
        # Get recent values for each metric
        for metric_name, metric_list in self.metrics.items():
            if metric_list:
                recent_metrics = self._get_recent_metrics(metric_name, minutes=10)
                if recent_metrics:
                    values = [m.value for m in recent_metrics]
                    summary["recent_metrics"][metric_name] = {
                        "count": len(values),
                        "latest_value": values[-1],
                        "min_value": min(values),
                        "max_value": max(values),
                        "avg_value": statistics.mean(values)
                    }
        
        return summary
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        return [
            {
                "id": alert.id,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
            for alert in self.active_alerts.values()
        ]
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            {
                "id": alert.id,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolution_time": alert.resolution_time.isoformat() if alert.resolution_time else None,
                "duration_minutes": (
                    (alert.resolution_time - alert.timestamp).total_seconds() / 60
                    if alert.resolution_time else None
                ),
                "metadata": alert.metadata
            }
            for alert in self.alerts
            if alert.timestamp >= cutoff_time
        ]
    
    def update_performance_counters(self, **kwargs):
        """Update performance counters."""
        for key, value in kwargs.items():
            if key in self.performance_counters:
                if key == "model_selections":
                    # Handle model selections dictionary
                    if isinstance(value, dict):
                        for model, count in value.items():
                            if model not in self.performance_counters["model_selections"]:
                                self.performance_counters["model_selections"][model] = 0
                            self.performance_counters["model_selections"][model] += count
                else:
                    self.performance_counters[key] = value
    
    async def stop_monitoring(self):
        """Stop all monitoring services."""
        self.running = False
        logger.info("Monitoring services stopped")