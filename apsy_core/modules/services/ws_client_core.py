import time
import json
import logging
import websocket
import platform
import socket
import uuid
import requests

from modules.services.ws_settings import get_setting, set_setting, sync_ws_mirrors

logger = logging.getLogger("ws-server-local")


def start_ws_client(config,shutdown_event):
    ws_url = f'{config["cloud"]["ws_url"]}connect'

    reconnect = config["cloud"].get("reconnect_seconds", 5)

    while True:
        ws = None
        last_log = 0
        
        try:
            logger.info("🌐 Conectando a WS Cloud: "+ws_url)
            ws = websocket.create_connection(ws_url, timeout=10)

            token = get_setting("cloud_token")

            if token:
                logger.info("🔑 Autenticando con token")
                ws.send(json.dumps({
                    "type": "auth",
                    "token": token
                }))
            else:
                logger.warning("🆕 Sin token, iniciando handshake")
                ws.send(json.dumps({
                    "type": "handshake",
                    "payload": get_identity(config,shutdown_event)
                }))

            _listen(ws,shutdown_event,config)

        except websocket.WebSocketAddressException:
            now = time.time()

            if now - last_log > 60:
                logger.warning("WS: sin conexión a internet")
                last_log = now

            time.sleep(5)

        except ConnectionRefusedError:
            # servidor caído
            logger.error("WS: servidor no disponible", exc_info=True)
            time.sleep(5)

        except Exception as e:
            logger.error(f"❌ WS error: {e}", exc_info=True)
            time.sleep(reconnect)

        finally:
            if ws:
                try:
                    ws.close()
                except Exception:
                    pass


def _listen(ws, shutdown_event, config):

    ws.settimeout(30)

    while not shutdown_event.is_set():
        try:
            msg = ws.recv()

            if not msg:
                raise Exception("WS cerrado")

            data = json.loads(msg)
            handle_message(data, shutdown_event, config, ws)

        except websocket.WebSocketTimeoutException:
            # mantener viva la conexión
            try:
                ws.ping()
            except:
                raise Exception("WS muerto")

        except websocket.WebSocketConnectionClosedException:
            raise Exception("WS cerrado")

        except Exception as e:
            raise e

def handle_message(data: dict,shutdown_event,config,ws):
    msg_type = data.get("type")

    #if msg_type == 'register_device_ok':
        #JSON ESPERADO
        #{
        #   "type": "register_device",
        #   "device_id": "uuid",
        #   "tipo": "caja",
        #   "nombre": "Caja 1"
        # }
        #guardar_device(data,config)

    if msg_type == "handshake_ok":
        logger.info("✅ Handshake exitoso")
        set_setting("cloud_token", data["token"])
        set_setting("ws_server_id", str(data["ws_server_id"]))
        sync_ws_mirrors(
            data["mirrors"]
        )

    elif msg_type == "auth_ok":
        logger.info("🔓 Autenticación correcta")

    elif msg_type == "cmd":
        logger.info(f"📩 Comando: {data}")
        # EJECUTAR COBROS, SYNC, UPDATES

    elif msg_type == "error":
        logger.error(f"❌ Error cloud: {data.get('message')}")
        # ⛔ error lógico → detener cliente
        shutdown_event.set()
        raise Exception("Error fatal desde cloud")

    elif msg_type == "mirror_api":
        response = local_api_proxy(data,config)

        ws.send(
        json.dumps({

            "type": "action_response",

            "request_id":
                data["request_id"],

            **response

        })
    )

    else:
        logger.warning(
            f"⚠️ Mensaje desconocido: {data}"
        )


def access_local(config, endpoint, payload=None):

    headers = {
        "Authorization": f"ApiKey {config['production_api']['access']['api_key']}",
        "X-Scope": config['production_api']['access']['scope'],
        "Content-Type": "application/json"
    }

    r = requests.post(
        f"{config['production_api']['base_url']}/{endpoint}",
        json=payload or {},
        headers=headers,
        timeout=config["production_api"]["timeout"]
    )

    try:

        r.raise_for_status()

    except requests.HTTPError as e:

        logger.error(f"API Error: {e}")
        
        return {
            "success": False,
            "error": str(e)
        }
    return r.json()


def get_identity(config,shutdown_event) -> dict:
    """
    Obtiene identidad del WS local + payload de sucursales desde API-Prod
    """

    logger.info("🔐 Obteniendo identidad desde API-Production")

    data = access_local(config,"internal/ws/identity")

    if not data.get("success"):
        shutdown_event.set() 
        raise Exception("API-Prod no devolvió identidad válida")

    payload = data.get("sucursales", [])

    if not payload:
        shutdown_event.set() 
        raise Exception("No hay sucursales asociadas a este servidor")

    identity = {
        "hostname": socket.gethostname(),
        "ip_local": socket.gethostbyname(socket.gethostname()),
        "mac": ":".join(f"{uuid.getnode():012x}"[i:i+2] for i in range(0, 12, 2)),
        "os": platform.system().lower(),
        "version": config["app"].get("version", "1.0.0"),
        "app": config["app"]["name"],
        "payload": payload
    }

    logger.info(f"✅ Identidad generada ({len(payload)} sucursal(es))")

    return identity

# def guardar_device(data, config):
#     import socket

#     # construir payload limpio
#     payload = {
#         "device_id": data.get("device_id"),
#         "tipo": data.get("tipo"),
#         "nombre": data.get("nombre"),
#         "ip": data.get("ip") or socket.gethostbyname(socket.gethostname()),
#         "mac": data.get("mac"),
#         "hostname": data.get("hostname"),
#         "os": data.get("os"),
#         "version": data.get("version"),
#         "app": data.get("app"),
#         "sucursal_id": data.get("sucursal_id")
#     }

#     # enviar al servidor (cmd 14 = registrar device)
#     try:
#         res = access_local(config,"internal/ws/register-device", payload)
#     except Exception as e:
#         logger.error(f"❌ Error registrando device: {e}")
#         return None

#     # validar respuesta
#     if not res.get("success"):
#         logger.error(f"Servidor rechazó dispositivo: {res.get("message")}")
#         return None

#     # guardar en ws_devices (LOCAL)
#     device = res.get("data", {})

#     guardar_en_ws_devices(device)

#     return device

def local_api_proxy(data,config):

    endpoint = data.get(
        "endpoint",
        ""
    )

    method = data.get(
        "method",
        "POST"
    ).upper()

    headers = data.get(
        "headers",
        {}
    )

    body = data.get(
        "body",
        {}
    )

    url = f"{config['production_api']['base_url']}{endpoint}"

    try:

        if method == "POST":

            r = requests.post(
                url,
                json=body,
                headers=headers,
                timeout=15
            )

        elif method == "GET":

            r = requests.get(
                url,
                params=body,
                headers=headers,
                timeout=15
            )

        else:

            return {

                "ok": False,

                "msg": f"Método no soportado: {method}"

            }

        try:

            return r.json()

        except Exception:

            return {

                "ok": r.ok,

                "status_code": r.status_code,

                "text": r.text

            }

    except Exception as e:

        return {

            "ok": False,

            "msg": str(e)

        }