from datetime import datetime, timedelta

from fastapi import APIRouter, Request

from modules.services.provisions import (
    create_session,
    validate_token_from_db,
    detect_onboarding_mode,
    get_ws_settings,
    register_terminal,
    create_tenant_auto,
    assign_trial_plan,
    get_tenant_by_device,
    get_updates,
    get_latest_version,
    get_install_credentials
)

import secrets


router = APIRouter(
    prefix="/provision",
    tags=["provision"]
)


@router.post("/init")
async def init(request: Request):

    body = await request.json()

    fingerprint = body.get("fingerprint")
    hostname = body.get("hostname")
    ip = body.get("ip")

    if not fingerprint:

        return {
            "ok": False,
            "msg": "missing fingerprint"
        }

    token = secrets.token_urlsafe(32)

    expires = datetime.utcnow() + timedelta(minutes=5)

    create_session(
        fingerprint,
        hostname,
        ip,
        token,
        expires
    )

    return {
        "ok": True,
        "token": token,
        "expires_in": 300
    }


@router.post("/device")
async def device(request: Request):

    token = request.headers.get(
        "Authorization",
        ""
    ).replace("Bearer ", "")

    body = await request.json()

    session = validate_token_from_db(token)

    if not session:

        return {
            "ok": False,
            "msg": "invalid session"
        }

    mode = detect_onboarding_mode(
        body["fingerprint"]
    )

    if mode == "new_device":

        tenant_id = create_tenant_auto(body)

        terminal_id = register_terminal(
            tenant_id,
            body
        )

        assign_trial_plan(
            tenant_id
        )

        crm_state = "new_customer"

    else:

        tenant_id = get_tenant_by_device(
            body["fingerprint"]
        )

        terminal_id = register_terminal(
            tenant_id,
            body
        )

        crm_state = "expansion"

    return {

        "ok": True,

        "credentials": get_install_credentials()

    }


@router.post("/update")
async def update(request: Request):

    token = request.headers.get(
        "Authorization",
        ""
    ).replace("Bearer ", "")

    body = await request.json()

    session = validate_token_from_db(token)

    if not session:

        return {
            "ok": False,
            "msg": "invalid session"
        }

    client_version = body.get(
        "version",
        "0.0.0.0"
    )

    return {

        "ok": True,

        "latest_version": get_latest_version(),

        "updates": get_updates(
            client_version
        )

    }