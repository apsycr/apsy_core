from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from modules.db import ejecutar, ejecutar_api
from modules.services.devices_token import validate_device_token

import secrets

router = APIRouter(
    prefix="/device",
    tags=["device"]
)

@router.post("/login")
async def register_device(
    request: Request
):
    body = await request.json()

    user = body.get(
        "user",
        ""
    ).strip()

    password = body.get(
        "password",
        ""
    ).strip()

    # ==========================================
    # VALIDATE INPUT
    # ==========================================

    if not user:

        return {

            "ok": False,

            "msg": "Usuario requerido"

        }

    if not password:

        return {

            "ok": False,

            "msg": "Contraseña requerida"

        }

    # ==========================================
    # VALIDATE DEVICE TOKEN
    # ==========================================

    device = validate_device_token(
        request
    )

    if not device:

        return {

            "ok": False,

            "msg": "Dispositivo no autorizado"

        }

    device = device['device']

    # ==========================================
    # DEVICE STATUS
    # ==========================================

    if device["estado"] != "accepted":

        return {

            "ok": False,

            "msg": "Dispositivo pendiente de autorización",

            "color": "orange"

        }

    # ==========================================
    # USER LOGIN
    # ==========================================

    rs = ejecutar_api(
        """
        SELECT

            u.id,
            u.user,
            u.nombre,
            u.idtipousuario             AS tipousuario,
            s.id                        AS idsucursal,
            s.nombre                    AS nombresucursal,
            s.cedula                    AS cedulasucursal,
            s.pfisico                   AS nombrefantasia,
            group_concat(t.telefono)    AS telefonosucursal,
            group_concat(c.correo)      AS correosucursal,
            s.idtiponegocio             AS tiposucursal

        FROM usuarios u

        INNER JOIN sucursales s
            ON s.id = u.idsucursal

        INNER JOIN correos c
            ON c.idfila = s.id
            and c.idtabla = 39

        INNER JOIN telefonos t
            ON t.idfila = s.id
            and t.idtabla = 39

        WHERE u.id > 0 and u.user = %s
        and u.clave = md5(aes_encrypt(%s,'lt6969'))
        """,
        (user,password),
        "one"
    )

    if not rs or rs['id'] == None:

        return {

            "ok": False,

            "msg": "Usuario o contraseña incorrectos"

        }

    # ==========================================
    # SESSION TOKEN
    # ==========================================

    session_token = secrets.token_urlsafe(
        48
    )

    ejecutar(
        """
        UPDATE ws_devices
           SET session_token=%s,
               idusuario=%s,
               last_login=NOW()
         WHERE id=%s
        """,
        (
            session_token,
            rs["id"],
            device["id"]
        ),
        'none'
    )

    # ==========================================
    # SUCCESS
    # ==========================================

    return {

        "ok": True,

        "msg": "Login correcto",

        "session_token": session_token,

        "user": {

            "idusuario": rs["id"],

            "nombreusuario": rs["nombre"],

            "tipousuario": rs["tipousuario"]

        },

        "company": {

            "idsucursal": rs["idsucursal"],

            "nombresucursal": rs["nombresucursal"],

            "cedulasucursal": rs["cedulasucursal"],

            "nombrefantasia": rs["nombrefantasia"],

            "telefonosucursal": rs["telefonosucursal"],

            "correosucursal": rs["correosucursal"],

            "tiposucursal": rs["tiposucursal"]

        }

    }


@router.post("/register")
async def register_device(
    request: Request
):

    # ==========================================
    # HEADERS
    # ==========================================

    auth = request.headers.get("Authorization", "")

    app = request.headers.get("X-App", "")

    version = request.headers.get("X-Version", "")

    from_mirror = request.headers.get(
        "x-from-mirror", 0)

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
            row["id"],

        ),"none")

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
            2 if from_mirror else 1

        ),"none")

        ws_device_id = ejecutar(
            "SELECT LAST_INSERT_ID() AS id",
            (),
            "one"
        )["id"]


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

            "estado": 'pending' if from_mirror else 'accepted'

        }

    }