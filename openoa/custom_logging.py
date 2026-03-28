import logging
import sys
from functools import wraps

def setup_logging(level='INFO'):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def set_log_level(level='INFO'):
    """Set logging level."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))



def logged_method_call(func):
    """Decorator for logging method calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger()
        logger.info(f"Starting {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise
    return wrapper
