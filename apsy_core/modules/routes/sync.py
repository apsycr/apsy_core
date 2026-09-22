from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from modules.services.sync.tools import check_token, sync_init, compile_pull_manifest, compile_push,sync_queue

router = APIRouter(
    prefix="/sync",
    tags=["sync"]
)

@router.post("/bootstrap")
def login(request: Request):
    #VALIDAR TOKEN
    token = request.headers.get("X-Token", "")
    tipo  = request.headers.get("X-Tipo", "")

    if token == '':
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "msg": "Error token requerido"
            }
        )
    
    device = check_token(token,tipo)

    if not device:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    return sync_init(tipo)

@router.post("/pull")
async def login(request: Request):
    #VALIDAR TOKEN
    token = request.headers.get("X-Token", "")
    tipo  = request.headers.get("X-Tipo", "")

    if token == '':
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "msg": "Error token requerido"
            }
        )
    
    device = check_token(token,tipo)

    if not device:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    body = await request.json()
    
    return compile_pull_manifest(body,tipo)

@router.post("/push")
async def push(request: Request):

    # VALIDAR TOKEN
    token = request.headers.get("X-Token", "")
    tipo  = request.headers.get("X-Tipo", "")

    if token == "":
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "msg": "Error token requerido"
            }
        )

    device = check_token(token, tipo)

    if not device:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    body = await request.json()

    return compile_push(body, tipo)

@router.post("/queue")
async def queue(request: Request):

    body = await request.json()

    return sync_queue(body)