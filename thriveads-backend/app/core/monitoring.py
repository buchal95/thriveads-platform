"""
Production monitoring and logging configuration
"""

import structlog
import logging
import sys
from typing import Dict, Any
from datetime import datetime
from contextlib import contextmanager
import time
import psutil
import os

from app.core.config import settings


def configure_logging():
    """Configure structured logging for production"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.ENVIRONMENT == "production" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )


class ApplicationMonitor:
    """Application performance and health monitoring"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.start_time = datetime.utcnow()
        self.request_count = 0
        self.error_count = 0
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            return {
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent
                },
                "cpu": {
                    "percent_used": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": round((disk.used / disk.total) * 100, 2)
                }
            }
        except Exception as e:
            self.logger.error("Failed to get system metrics", error=str(e))
            return {}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        uptime = datetime.utcnow() - self.start_time
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_human": str(uptime),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": (self.error_count / max(self.request_count, 1)) * 100,
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0"
        }
    
    @contextmanager
    def monitor_request(self, endpoint: str):
        """Context manager to monitor request performance"""
        start_time = time.time()
        self.request_count += 1
        
        try:
            yield
            duration = time.time() - start_time
            
            self.logger.info(
                "Request completed",
                endpoint=endpoint,
                duration_ms=round(duration * 1000, 2),
                status="success"
            )
            
        except Exception as e:
            self.error_count += 1
            duration = time.time() - start_time
            
            self.logger.error(
                "Request failed",
                endpoint=endpoint,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                status="error"
            )
            raise
    
    def log_meta_api_call(self, endpoint: str, duration: float, status_code: int, response_size: int = 0):
        """Log Meta API call metrics"""
        self.logger.info(
            "Meta API call",
            endpoint=endpoint,
            duration_ms=round(duration * 1000, 2),
            status_code=status_code,
            response_size_bytes=response_size,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_database_query(self, query_type: str, duration: float, records_affected: int = 0):
        """Log database query metrics"""
        self.logger.info(
            "Database query",
            query_type=query_type,
            duration_ms=round(duration * 1000, 2),
            records_affected=records_affected,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log application errors with context"""
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if context:
            error_context.update(context)
        
        self.logger.error("Application error", **error_context)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        self.logger.warning(
            "Security event",
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            **details
        )


# Global monitor instance
monitor = ApplicationMonitor()


def get_monitor() -> ApplicationMonitor:
    """Get the global monitor instance"""
    return monitor


# Configure logging on import
configure_logging()
