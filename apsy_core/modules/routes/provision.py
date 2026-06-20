from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from services.provisions import (
    validate_init_token,
    get_ws_settings,
    register_terminal,
    build_crm_initial
)

import secrets
import time

router = APIRouter(
    prefix="/provision",
    tags=["provision"]
)

INSTALL_TOKENS = {}

@router.post("/provision/init")
async def init(request: Request):

    body = await request.json()

    fingerprint = body.get("fingerprint")
    hostname = body.get("hostname")
    ip = body.get("ip")

    if not fingerprint:
        return {"ok": False, "msg": "missing fingerprint"}

    token = secrets.token_urlsafe(32)

    expires = datetime.utcnow() + timedelta(minutes=5)

    create_session(fingerprint, hostname, ip, token, expires)

    return {
        "ok": True,
        "token": token,
        "expires_in": 300
    }   

@router.post("/provision/device")
async def provision_device(request: Request):

    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    body = await request.json()

    session = validate_token_from_db(token)

    if not session:
        return {"ok": False, "msg": "invalid session"}

    mode = detect_onboarding_mode(body["fingerprint"])

    # 1. NUEVO CLIENTE COMPLETO
    if mode == "new_device":

        tenant_id = create_tenant_auto(body)

        terminal_id = register_terminal(tenant_id, body)

        plan = assign_trial_plan(tenant_id)

        crm_state = "new_customer"

    # 2. CLIENTE EXISTENTE
    else:

        tenant_id = get_tenant_by_device(body["fingerprint"])

        terminal_id = register_terminal(tenant_id, body)

        crm_state = "expansion"

    # WS SETTINGS SIEMPRE
    return {
        "ok": True,

        "mode": mode,

        "crm": {
            "tenant_id": tenant_id,
            "state": crm_state
        },

        "service": {
            "ws_settings": get_ws_settings()
        },

        "schemas": {
            "ws_local": get_schema("ws_local"),
            "production": get_schema("production")
        }
    }