import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

default_formatter = logging.Formatter("%(asctime)s: %(levelname)s: %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(default_formatter)

logger.addHandler(console_handler)
