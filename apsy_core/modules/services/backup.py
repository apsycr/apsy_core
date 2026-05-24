import os
import logging
from datetime import datetime
from pathlib import Path

from modules.config import load_config

logger = logging.getLogger("ws-server-local")

def validar_backup():
    config = load_config()

    backup_cfg = config.get("backup", {})
    scheduler_cfg = config.get("scheduler", {}).get("jobs", {}).get("backup_db", {})

    if not scheduler_cfg.get("enabled", False):
        logger.info("Backup deshabilitado por configuración")
        return False

    # Hora programada
    hora_backup = scheduler_cfg.get("time", "02:00")
    ahora = datetime.now().strftime("%H:%M")

    if ahora != hora_backup:
        return False

    target = scheduler_cfg.get("target", "filesystem")

    try:
        if target == "dropbox":
            ejecutar_backup_dropbox(backup_cfg)
        else:
            ejecutar_backup_local(backup_cfg)

        logger.info("Backup ejecutado correctamente")
        return True

    except Exception as e:
        logger.error(f"Error en backup: {e}", exc_info=True)
        return False
