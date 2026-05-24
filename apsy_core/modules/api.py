from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import logging

from modules.routes import auth, site, sync, proc, core, internal
from modules.ws.router import router as ws_router
from modules.db import ejecutar_api

logger = logging.getLogger("ws-server-local")


def start_api(config):

    app = FastAPI(title="Apsy_Core")
    API_PREFIX = ""

    # =====================================
    # 🔐 AUTH MIDDLEWARE
    # =====================================
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):

        public_paths = [
            "/login",
            "/docs",
            "/openapi.json",
            "/health",
            "/ws/"
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

    logger.info(f'[API] ejecutando en {config["api"]["host"]}:{config["api"]["port"]}')

    uvicorn.run(
        app,
        host=config["api"]["host"],
        port=config["api"]["port"],
        log_level="warning"
    )