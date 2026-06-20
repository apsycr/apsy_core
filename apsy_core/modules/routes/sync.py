from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from modules.services.sync.tools import check_token, sync_init, compile_pull_manifest

router = APIRouter(
    prefix="/sync",
    tags=["sync"]
)

@router.post("/bootstrap")
def login(request: Request):
    #VALIDAR TOKEN
    token = request.headers.get("X-Token", "")

    if token == '':
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "msg": "Error token requerido"
            }
        )
    
    device = check_token(token)

    if not device:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    return sync_init(device)

@router.post("/pull")
async def login(request: Request):
    #VALIDAR TOKEN
    token = request.headers.get("X-Token", "")

    if token == '':
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "msg": "Error token requerido"
            }
        )
    
    device = check_token(token)

    if not device:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    body = await request.json()

    return compile_pull_manifest(device,body)