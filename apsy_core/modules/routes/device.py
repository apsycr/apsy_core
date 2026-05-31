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

            "msg": "Dispositivo pendiente autorización"

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
            u.idtipousuario,
            s.id                        AS idsucursal,
            s.nombre                    AS nombresucursal,
            s.cedula                    AS cedulasucursal,
            s.pfisico                   AS nombrefantasia,
            group_concat(t.telefono)    AS telefonosucursal,
            group_concat(c.correo)       AS correosucursal,
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

        WHERE u.id > 0 and u.usuario = %s
        and s.clave = md5(aes_encrypt(%s,'lt6969'))
        """,
        (user,password),
        "one"
    )

    if not rs:

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

    db.execute(
        """
        UPDATE ws_devices
           SET session_token=%s,
               idusuario=%s,
               last_login=NOW()
         WHERE id=%s
        """,
        [
            session_token,
            rs["id"],
            device["id"]
        ]
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

        ),"none")

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

            "estado": 'accepted'

        }

    }