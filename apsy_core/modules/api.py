from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime

import uvicorn
import logging
import secrets

from modules.routes import auth, site, sync, proc, core, internal
from modules.ws.router import router as ws_router
from modules.db import ejecutar_api, ejecutar

logger = logging.getLogger("ws-server-local")

def start_api(config):

    app = FastAPI(title="Apsy_Core")
    API_PREFIX = ""

    # =====================================
    # 🔐 AUTH MIDDLEWARE
    # =====================================
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):

        mirror = request.headers.get("X-Mirror")

        if mirror:

            response = await mirror_manager.proxy_request(
                mirror,
                request
            )

            return JSONResponse(response)

        public_paths = [
            "/login",
            "/docs",
            "/openapi.json",
            "/health",
            "/ws/",
            "/internal/",
            "/ping",
            "/register-device"
        ]

        if any(request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)

        token = request.cookies.get("apsy_token")

        if not token:
            return JSONResponse(
                status_code=401,
                content={"ok": 0, "msg": "Token requerido"}
            )

        try:
            row = ejecutar_api("""
                SELECT 
                    t.user_id,
                    t.sucursal_id,
                    t.device_id,
                    t.expires_at,
                    u.nombre AS user_nombre,
                    s.nombre AS sucursal_nombre,
                    s.idtiponegocio as negocio
                FROM auth_tokens t
                JOIN usuarios u ON u.id = t.user_id
                JOIN sucursales s ON s.id = t.sucursal_id
                WHERE t.token = %s
                LIMIT 1
            """, (token,),'one')
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"ok": 0, "msg": f"Error validando token: {str(e)}"}
            )

        if not row:
            return JSONResponse(
                status_code=401,
                content={"ok": 0, "msg": "Token inválido"}
            )

        # =====================================
        # ⏳ EXPIRACIÓN (solo WEB)
        # =====================================
        if row["expires_at"] is not None:
            from datetime import datetime
            if row["expires_at"] < datetime.now():
                return JSONResponse(
                    status_code=401,
                    content={"ok": 0, "msg": "Token expirado"}
                )

        # =====================================
        # 🔥 INYECTAR CONTEXTO
        # =====================================
        request.state.user_id = row["user_id"]
        request.state.sucursal_id = row["sucursal_id"]
        request.state.device_id = row["device_id"]
        request.state.user_nombre = row["user_nombre"]
        request.state.sucursal_nombre = row["sucursal_nombre"]
        request.state.tipo_negocio = row["negocio"]


        # =====================================
        # 🔄 UPDATE ACTIVITY
        # =====================================
        try:
            ejecutar_api("""
                UPDATE auth_tokens
                SET last_activity = NOW()
                WHERE token = %s
            """, (token,),'none',request)
        except:
            pass  # no romper flujo por esto

        return await call_next(request)

    # =====================================
    # ❌ 404 CUSTOM
    # =====================================
    @app.exception_handler(404)
    async def custom_404_handler(request: Request, exc):
        print(f"❌ NOT FOUND: {request.url}")
        return JSONResponse(
            status_code=404,
            content={
                "ok": 0,
                "msg": "Ruta no encontrada",
                "path": str(request.url)
            }
        )

    # =====================================
    # 📦 ROUTES
    # =====================================
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(site.router, prefix=API_PREFIX)
    app.include_router(sync.router, prefix=API_PREFIX)
    app.include_router(proc.router, prefix=API_PREFIX)
    app.include_router(core.router, prefix=API_PREFIX)
    app.include_router(internal.router, prefix=API_PREFIX)

    # =====================================
    # WS
    # =====================================
    if config["ws_server"]["enabled"]:
        
        app.include_router(ws_router)
        logger.info("🌐 WebSocket habilitado")

    # =====================================
    # ❤️ HEALTH
    # =====================================
    @app.get("/health")
    def health():
        return {"status": "ok"}

    # =====================================
    # 🖨 PRINT
    # =====================================
    @app.post("/print")
    def print_job(data: dict):
        logger.info(f"Print request: {data}")
        return {"result": "sent"}

    # =====================================
    # 🔄 SYNC
    # =====================================
    @app.post("/sync/register")
    def sync_register(data: dict):
        logger.info(f"Caja registrada: {data}")
        return {"status": "registered"}

    @app.post("/sync/push")
    def sync_push(data: dict):
        logger.info(f"SYNC push: {data}")
        return {"status": "received"}

    @app.get("/sync/status")
    def sync_status():
        return {
            "ws": "online",
            "cloud": "connected"
        }

    @app.get("/ping")
    async def ping():
        return {
            "ok": True,
            "mirror": "CR-01",
            "version": "1.0.0",
            "empresa": "APSYCR",
            "timezone": "-06:00"
        }

    @app.post("/register-device")
    async def register_device(
        request: Request
    ):

        import secrets

        # ==========================================
        # HEADERS
        # ==========================================

        auth = request.headers.get("Authorization", "")

        app = request.headers.get("X-App", "")

        version = request.headers.get("X-Version", "")

        # ==========================================
        # VALIDATE CLIENT
        # ==========================================

        if auth != "Bearer APSY_PAIR_V1":

            return JSONResponse(
                status_code=401,
                content={
                    "ok": False,
                    "msg": "Unauthorized"
                }
            )

        if app == "":

            return JSONResponse(
                status_code=401,
                content={
                    "ok": False,
                    "msg": "Invalid app"
                }
            )

        # ==========================================
        # BODY
        # ==========================================

        body = await request.json()

        mirror = body.get(
            "mirror",
            ""
        ).strip()

        requires_pair = bool(
            body.get(
                "requires_pair",
                False
            )
        )

        device = body.get(
            "device",
            {}
        )

        # ==========================================
        # DEVICE DATA
        # ==========================================

        device_id = device.get(
            "device_id",
            ""
        ).strip()

        nombre = device.get(
            "nombre",
            ""
        ).strip()

        hostname = device.get(
            "hostname",
            ""
        ).strip()

        ip = device.get(
            "ip",
            ""
        ).strip()

        mac = device.get(
            "mac",
            ""
        ).strip()

        platform = device.get(
            "platform",
            ""
        ).strip()

        os_version = device.get(
            "os_version",
            ""
        ).strip()

        # ==========================================
        # VALIDATE DEVICE
        # ==========================================

        if device_id == "":

            return {
                "ok": False,
                "msg": "device_id requerido"
            }

        # ==========================================
        # MIRROR DATA
        # ==========================================

        sucursal_id = 0

        mirror_alias = ""

        row_mirror = None

        if requires_pair:

            if mirror == "":

                return {
                    "ok": False,
                    "msg": "Mirror requerido"
                }

            row_mirror = ejecutar("""

                SELECT
                    id,
                    ws_server_id,
                    activo
                FROM ws_sucursales
                WHERE alias = %s
                LIMIT 1

            """, (mirror,), "one")

            if not row_mirror:

                return {
                    "ok": False,
                    "msg": "Mirror no existe"
                }

            if row_mirror["activo"] != 1:

                return {
                    "ok": False,
                    "msg": "Mirror inactivo"
                }

            if not mirror_manager.exists(
                row_mirror["ws_server_id"]
            ):

                return {
                    "ok": False,
                    "msg": "Mirror offline"
                }

            sucursal_id = row_mirror["id"]

            mirror_alias = mirror

        # ==========================================
        # TOKEN
        # ==========================================

        token = secrets.token_hex(32)

        # ==========================================
        # EXIST DEVICE
        # ==========================================

        row = ejecutar("""

            SELECT
                id,
                estado
            FROM ws_devices
            WHERE device_id = %s
            LIMIT 1

        """, (device_id,), "one")

        # ==========================================
        # UPDATE DEVICE
        # ==========================================

        if row:

            ejecutar("""

                UPDATE ws_devices SET

                    nombre = %s,
                    hostname = %s,
                    ip = %s,
                    mac = %s,
                    app = %s,
                    version = %s,
                    platform = %s,
                    os_version = %s,
                    token = %s,
                    mirror = %s,
                    sucursal_id = %s,
                    last_seen = NOW()

                WHERE id = %s

            """, (

                nombre,
                hostname,
                ip,
                mac,
                app,
                version,
                platform,
                os_version,
                token,
                mirror_alias,
                sucursal_id,
                row["id"]

            ))

            ws_device_id = row["id"]

        else:

            ejecutar("""

                INSERT INTO ws_devices (

                    device_id,
                    nombre,
                    hostname,
                    ip,
                    mac,
                    app,
                    version,
                    platform,
                    os_version,
                    token,
                    estado,
                    mirror,
                    sucursal_id,
                    created_at,
                    last_seen

                ) VALUES (

                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    1,
                    %s,
                    %s,
                    NOW(),
                    NOW()

                )

            """, (

                device_id,
                nombre,
                hostname,
                ip,
                mac,
                app,
                version,
                platform,
                os_version,
                token,
                mirror_alias,
                sucursal_id

            ))

            ws_device_id = ejecutar(
                "SELECT LAST_INSERT_ID() AS id",
                (),
                "one"
            )["id"]

        # ==========================================
        # OPTIONAL MIRROR PAIR
        # ==========================================

        if requires_pair:

            try:

                response = await mirror_manager.proxy_request(

                    row_mirror["ws_server_id"],

                    {

                        "type": "action",

                        "action": "pair_device",

                        "device": device

                    },

                    timeout=20

                )

                if not response.get("ok"):

                    return response

            except Exception as e:

                print(e)

                return {
                    "ok": False,
                    "msg": "Error comunicando mirror"
                }

        # ==========================================
        # SUCCESS
        # ==========================================

        return {

            "ok": True,

            "msg": "Device registrado",

            "device": {

                "id": ws_device_id,

                "device_id": device_id,

                "token": token,

                "estado": 1

            }

        }

    logger.info(f'[API] ejecutando en {config["api"]["host"]}:{config["api"]["port"]}')

    uvicorn.run(
        app,
        host=config["api"]["host"],
        port=config["api"]["port"],
        log_level="warning"
    )