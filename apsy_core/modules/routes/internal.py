from fastapi import APIRouter, Request

router = APIRouter(prefix="/internal")

@router.post("/ws/identity")
def ws_identity(request: Request):

    # validar api key
    # validar scope

    return {
        "success": 1,
        "sucursales": [...]
    }

@router.post("/ws/register-device")
def ws_identity(request: Request):

    # validar api key
    # validar scope

    return {
        "success": 1,
        "sucursales": [...]
    }