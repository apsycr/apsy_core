import threading
import time
import logging
import signal
#import sys
from pathlib import Path

from modules.api import start_api
from modules.ws_client import start_ws_client
from modules.health import health_loop
from modules.config import load_config

from modules.scheduler import start as start_scheduler, add_cron
from modules.startup import on_startup
from modules.services.irobot import leer_correos

#from modules.ws_server import start_ws_server

from modules.db import init_pools

#BASE_DIR = Path(sys.executable if getattr(sys, 'frozen', False) else __file__).parent

LOG_DIR = Path("/logs")

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

logging.basicConfig(
    filename=LOG_DIR / "ws-server-local.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("ws-server-local")

shutdown_event = threading.Event()

def shutdown_handler(signum, frame):
    logger.info("Shutdown signal received")
    shutdown_event.set()

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)


def main():
    logger.info("Starting APSY_CORE")
    config = load_config()
    init_pools() #INICIALIZAR BASE DE DATOS
    
    # -------- STARTUP (cambio de día)
    on_startup()

    # -------- Scheduler
    if config["services"]["irobot"]["enabled"]:
        add_cron(
            leer_correos,
            config["services"]["irobot"]["hours"],
            "irobot_mail"
        )

    start_scheduler()

    # -------- Threads existentes

    api_thread = threading.Thread(
        target=start_api,
        args=(config,),
        daemon=True
    )

    if config['ws_server']['client']:
        ws_thread = threading.Thread(
            target=start_ws_client,
            args=(config,shutdown_event,),
            daemon=True
        )


        ws_thread.start()

    health_thread = threading.Thread(
        target=health_loop,
        args=(config,),
        daemon=True
    )

    #ws_server_thread = threading.Thread(
    #    target=start_ws_server,
    #    args=(config,),
    #    daemon=True
    #)

    api_thread.start()
    health_thread.start()
    #ws_server_thread.start()

    logger.info("All services started")

    while not shutdown_event.is_set():
        time.sleep(1)

    logger.info("Stopping ws-server-local")


if __name__ == "__main__":
    main()
