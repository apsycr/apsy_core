from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
import logging
import secrets

from modules.routes import auth, site, sync, proc, core, internal, device, gateway, oauth, provision, mail
from modules.ws.router import router as ws_router
from modules.db import ejecutar_api, ejecutar

logger = logging.getLogger("ws-server-local")

def start_api(config):

    app = FastAPI(title="Apsy_Core")
    API_PREFIX = ""

    # =====================================
    # 🔐 AUTH MIDDLEWARE
    # =====================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://apsycr.com",
            "https://www.apsycr.com",
        ],
        allow_origin_regex=r"https?://(127\.0\.0\.1|localhost)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):

        mirror = request.headers.get("X-Mirror")

        path = request.url.path

        if mirror:
            from modules.services.mirror_manager import mirror_manager

            mirror = mirror_manager.validar_mirror(mirror)

            if mirror['ok']:

                try:

                    response = await mirror_manager.send_api(

                        mirror["ws_server_id"],

                        endpoint=path,

                        body=await request.json(),

                        headers=request.headers,

                        timeout=20

                    )

                    return JSONResponse(
                        status_code=200,
                        content=response
                    )

                except Exception as e:

                    print(e)

                    return JSONResponse(
                        status_code=401,
                        content={
                            "ok": False,
                            "msg": "Error comunicando mirror"
                        }
                    )
            else:
                return JSONResponse(
                    status_code=401,
                    content={
                        "ok": False,
                        "msg": mirror['msg']
                    }
                )

        public_paths = [
            "/login",
            "/docs",
            "/openapi.json",
            "/health",
            "/ws/",
            "/internal/",
            "/ping",
            "/device/register",
            "/auth/refresh",
            "/auth/code",
            "/mail/code",
            "/oauth/",
            "/sync/",
            "/provision/",
            "/download/"
        ]

        if any(path.startswith(p) for p in public_paths):
            return await call_next(request)

        # =====================================
        # DEVICE AUTH
        # =====================================

        if path.startswith("/device"):

            auth = request.headers.get(
                "Authorization",
                ""
            )

            token = auth.replace(
                "Bearer ",
                ""
            ).strip()

            if token == "":

                return JSONResponse(
                    status_code=401,
                    content={
                        "ok": False,
                        "msg": "Token requerido",
                    }
                )

            device = ejecutar("""

                SELECT
                    id,
                    estado
                FROM ws_devices
                WHERE token = %s
                LIMIT 1

            """, (

                token,

            ), "one")

            if not device:

                return JSONResponse(
                    status_code=401,
                    content={
                        "ok": False,
                        "msg": "Token inválido"
                    }
                )

            request.state.device = device

            return await call_next(request)

        token = request.cookies.get("apsy_token")

        if not token:
            return JSONResponse(
                status_code=401,
                content={"ok": 0, "msg": "Token requerido","error":"token_deleted"}
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
                    content={
                        "ok": 0,
                        "error": "token_expired",
                        "refresh_required": True
                    }
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
    app.include_router(gateway.router, prefix=API_PREFIX)
    app.include_router(oauth.router, prefix=API_PREFIX)
    app.include_router(provision.router, prefix=API_PREFIX)
    app.include_router(mail.router, prefix=API_PREFIX)
    app.include_router(device.router)

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


    @app.get("/ping")
    async def ping():
        return {
            "ok": True,
            "version": "1.0.0",
            "empresa": "APSYCR",
            "timezone": "-06:00"
        }


    @app.post("/auth/refresh")
    async def refresh_token(
        request: Request
    ):

        refresh_token = request.cookies.get(
            "apsy_refresh"
        )

        if not refresh_token:

            return JSONResponse(
                status_code=401,
                content={
                    "ok": 0,
                    "error": "refresh_missing"
                }
            )

        from datetime import datetime, timedelta
        from modules.db import ejecutar_api
        from modules.routes.auth import generar_token

        row = ejecutar_api(
            """
            SELECT
                user_id,
                sucursal_id,
                device_id,
                refresh_expires_at
            FROM auth_tokens
            WHERE refresh_token = %s
            """,
            (refresh_token,),
            'one'
        )

        if not row:

            return JSONResponse(
                status_code=401,
                content={
                    "ok": 0,
                    "error": "refresh_invalid"
                }
            )


        if row["refresh_expires_at"] < datetime.now():

            return JSONResponse(
                status_code=401,
                content={
                    "ok": 0,
                    "error": "refresh_expired"
                }
            )

        # =====================================
        # Generar nuevos tokens
        # =====================================

        new_access_token = generar_token()
        new_refresh_token = generar_token()

        access_expires_at = (
            datetime.now() +
            timedelta(hours=2)
        )

        refresh_expires_at = (
            datetime.now() +
            timedelta(days=30)
        )

        ejecutar_api(
            """
             UPDATE auth_tokens
            SET
                token = %s,
                refresh_token = %s,
                expires_at = %s,
                refresh_expires_at = %s,
                last_activity = NOW()
            WHERE refresh_token = %s
            """,
            (
                new_access_token,
                new_refresh_token,
                access_expires_at,
                refresh_expires_at,
                refresh_token
            ),
            'none'
        )


        response = JSONResponse(
            content={
                "ok": 1
            }
        )

        is_https = request.url.scheme == "https"

        response.set_cookie(
            key="apsy_token",
            value=new_access_token,
            httponly=True,
            secure=is_https,
            samesite="Lax"
        )

        response.set_cookie(
            key="apsy_refresh",
            value=new_refresh_token,
            httponly=True,
            secure=is_https,
            samesite="Lax"
        )

        return response

    logger.info(f'[API] ejecutando en {config["api"]["host"]}:{config["api"]["port"]}')

    uvicorn.run(
        app,
        host=config["api"]["host"],
        port=config["api"]["port"],
        log_level="warning"
    )