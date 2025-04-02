import logging
from warnings import filterwarnings
filterwarnings("ignore", category=RuntimeWarning)
filterwarnings("ignore", category=DeprecationWarning)

# ignore urllib3.connectionpool
connectionpool_logger = logging.getLogger("urllib3.connectionpool")
connectionpool_logger.setLevel(logging.CRITICAL)
