import asyncio
import websockets
import json
import secrets
import requests

from modules.services.ws_settings import guardar_en_ws_devices

clients = set()

class LocalAPI:

    def __init__(self, config):
        self.base_url = config["production_api"]["base_url"]
        self.timeout = config["production_api"]["timeout"]
        self.headers = {
            "Authorization": f"ApiKey {config['production_api']['access']['api_key']}",
            "X-Scope": config['production_api']['access']['scope'],
            "Content-Type": "application/json"
        }

    def _request(self, cmd, payload=None):
        r = requests.post(
            self.base_url,
            json={"cmd": cmd, "data": payload or {}},
            headers=self.headers,
            timeout=self.timeout
        )
        r.raise_for_status()
        return r.json()

async def handler(ws):

    try:
        async for msg in ws:

            data = json.loads(msg)
            tipo = data.get("type")

            if tipo == "auth":
                await handle_auth(ws, data)

            elif tipo == "register_device":
                await handle_register(ws, data)

            elif tipo == "ping":
                await ws.send(json.dumps({"type": "pong"}))

            else:
                print("⚠️ MSG:", data)

    except Exception as e:
        print("❌ WS ERROR:", e)

    finally:
        clients.remove(ws)

async def handle_auth(ws, data):

    token = data.get("token")
    res = None
    # validar contra DB local
    # with get_db() as db:
    #     res = db.query(
    #         "SELECT * FROM device_config WHERE token=?",
    #         [token]
    #     )

    if res:
        await ws.send(json.dumps({
            "type": "auth_ok"
        }))
    else:
        await ws.send(json.dumps({
            "type": "error",
            "message": "Token inválido"
        }))

async def handle_register(ws, data):

    device = data.get("data")

    #VALIDAR SI LA MAC EXISTE DEVOLVER TOKEN
    #        SI EL ESTADO ESTA MARCADO COMO INACTIVO TOKEN VACIO
    #        SI LA CANTIDAD DE CONEXIONES SIMULTANEAS SUPERAN EL PLAN ASOCIADO DEVOLVER ERROR DE PLAN

    

    token = secrets.token_hex(32)

    device['token'] = token
    device['sucursal_id'] = 0
    guardar_en_ws_devices(device)

    await ws.send(json.dumps({
            "type":"register_device_ok",
            "devuelta": data,
            "token":token
        }))
    #with get_db() as db:

    #     db.query("""
    #         INSERT INTO device_config
    #         (device_id, token, tipo, sucursal_id, registrado)
    #         VALUES (?, ?, ?, ?, 1)
    #         """, [
    #         device.get("device_id"),
    #         token,
    #         device.get("tipo"),
    #         1
    #     ])

    # await ws.send(json.dumps({
    #     "type": "register_device_ok",
    #     "token": token,
    #     "device_id": device.get("device_id"),
    #     "tipo": device.get("tipo"),
    #     "sucursal_id": 1
    # }))

async def main(host="0.0.0.0", port=8443): #PUERTO SUJERIDO LOCAL 8765
    async with websockets.serve(handler, host, port):
        print(f"🌐 WS SERVER LOCAL {host}:{port}")
        await asyncio.Future()  # run forever


def start_ws_server(config):

    asyncio.run(
        main(
            config["ws_server"]["host"],
            config["ws_server"]["port"]
        )
    )