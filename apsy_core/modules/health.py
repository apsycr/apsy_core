import time
import logging

logger = logging.getLogger("ws-server-local")

def health_loop(config):
    while True:
        logger.debug("Health OK")
        time.sleep(30)
