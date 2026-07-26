"""Constants for the Receipt Printer integration."""
DOMAIN = "receipt_printer"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_FAST = "fast"

DEFAULT_PORT = 8000

# Data keys accepted on the notify service call
DATA_IMAGE_URL = "image_url"
DATA_TASK_TYPE = "task_type"
DATA_FAST = "fast"

# Endpoint paths on the api.py service
ENDPOINT_TEXT = "/print/text"
ENDPOINT_URL = "/print/url"
ENDPOINT_TASK = "/print/task"
ENDPOINT_IMAGE = "/print/image"