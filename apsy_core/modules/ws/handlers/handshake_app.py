#from modules.ws.repositories.ws_app_repo import upsert_device
from modules.services.ws_settings import guardar_en_ws_devices
import secrets

async def handle_app_handshake(websocket, identity):

    validar_app(identity)

    identity['token'] = secrets.token_hex(32)

    device = guardar_en_ws_devices(identity)

    await websocket.send_json({
        "type": "register_device_ok",
        "success": 1,
        "token": device["token"],
        "device_id": device["device_id"],
        "sucursal_id": device["sucursal_id"]
    })

def validar_app(data: dict):
    required = ["hostname", "mac", "os", "app", "version"]

    for k in required:
        if k not in data:
            raise Exception(f"Falta campo {k}")
