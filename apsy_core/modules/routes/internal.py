from fastapi import APIRouter, Request
import socket
import uuid
import platform
from modules.db import ejecutar_api

router = APIRouter()

API_KEY = "APSY-LOCAL-123456"
API_SCOPE = "ws-server-local"

@router.post("/internal/ws/identity")
async def ws_identity(request: Request):
    auth = request.headers.get("Authorization")
    scope = request.headers.get("X-Scope")

    if auth != f"ApiKey {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API Key")

    if scope != API_SCOPE:
        raise HTTPException(status_code=401, detail="Invalid Scope")

    info_sucursales = ejecutar_api("""
            SELECT 
                id,
                cedula,
                nombre,
                pfisico
            from 
                sucursales
            where id >= 0;
        """,(),'all')
    
    payload = []

    for row in info_sucursales:

        payload.append({
            "idsucursal": row["id"],
            "nombre": row["nombre"],
            "cedula": row["cedula"],
            "razon": row["pfisico"],
            "access_token": "" #generar_access_token(row)
        })

    return {
        "success": True,
        "sucursales": payload,
        "identity": {
            "hostname": socket.gethostname(),
            "ip_local": socket.gethostbyname(socket.gethostname()),
            "mac": ":".join(
                f"{uuid.getnode():012x}"[i:i+2]
                for i in range(0, 12, 2)
            ),
            "os": platform.system().lower()
        }
    }

@router.post("/internal/ws/register-device")
def ws_identity(request: Request):

    # validar api key
    # validar scope

    return {
        "success": 1,
        "sucursales": []
    }