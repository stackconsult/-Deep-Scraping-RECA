import logging
import sys
import os
from typing import Optional
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter to standardize log output.
    """
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp if not present
        if not log_record.get('timestamp'):
            from datetime import datetime
            log_record['timestamp'] = datetime.utcnow().isoformat()
            
        # Standardize level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

def setup_logging(
    log_level: str = "INFO",
    enable_json: bool = False,
    service_name: str = "orchestra-agent"
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (INFO, DEBUG, etc.)
        enable_json: Whether to output logs in JSON format
        service_name: Name of the service for log identification
    """
    # Get root logger
    logger = logging.getLogger()
    
    # clear existing handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)
        
    # Set level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    if enable_json:
        # JSON formatting for production
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Standard readable formatting for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log startup
    logging.getLogger(__name__).info(
        f"Logging configured",
        extra={
            "service": service_name, 
            "level": log_level, 
            "json_enabled": enable_json
        }
    )
