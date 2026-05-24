import requests
import logging
import platform
import socket
import uuid

from modules.services.ws_settings import set_setting

logger = logging.getLogger("ws-server-local")

def ejecutar_handshake(config):
    prod_url = config["production_api"]["base_url"]
    cloud_url = config["cloud"]["ws_url"]

    # -------------------------
    # 1) Obtener bearer producción
    # -------------------------
    logger.info("Obteniendo bearer desde API-Production")

    headers = {
        "Authorization": f"ApiKey {config['production_api']['access']['api_key']}",
        "X-Scope": config['production_api']['access']['scope']
    }

    r = requests.post(
        config["production_api"]["base_url"],
        json={"cmd": 13},
        headers=headers,
        timeout=10
    )
    r.raise_for_status()

    bearer = r.json()["token"]

    # -------------------------
    # 2) Fingerprint local
    # -------------------------
    hostname = socket.gethostname()

    payload = {
        "hostname": hostname,
        "os": platform.platform(),
        "ip_local": socket.gethostbyname(hostname),
        "mac": hex(uuid.getnode()),
        "version": config["app"].get("version", "1.0.0"),
        "timezone": config["app"].get("timezone", "UTC")
    }

    # -------------------------
    # 3) Handshake WS-Cloud
    # -------------------------
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Client-Type": "ws-server-local"
    }

    logger.info("Ejecutando handshake con WS-Cloud")

    ws = websocket.WebSocket()
    ws.connect(
        ws_url,
        header=[f"{k}: {v}" for k, v in headers.items()],
        timeout=10
    )

    data = r.json()

    # -------------------------
    # 4) Guardar token WS
    # -------------------------
    set_setting("cloud_token", data["token"])
    set_setting("cloud_registered", "1")
    set_setting("ws_id", str(data["ws_id"]))
    set_setting("sucursal_id", str(data["sucursal_id"]))

    logger.info("Handshake exitoso")

    return data["token"]
