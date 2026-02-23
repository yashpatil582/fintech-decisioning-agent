import logging, sys
from app.utils.config import settings

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    for lib in ("boto3", "botocore", "urllib3"):
        logging.getLogger(lib).setLevel(logging.WARNING)
