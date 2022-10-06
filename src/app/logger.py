import logging

DEFAULT_LOGGER = logging.getLogger("app")
DEFAULT_LOGGER.setLevel(logging.DEBUG)
DEFAULT_LOGGER.addHandler(logging.StreamHandler())
