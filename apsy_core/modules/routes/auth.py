from fastapi import APIRouter, HTTPException, Depends, Response, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from modules.db import ejecutar_api
import hashlib
import secrets
import uuid
import time

router = APIRouter()

def resolve_redirect(user, sucursal, login_type):

    tipo_negocio = sucursal["idtiponegocio"]
    tipo_usuario = user["idTipoUsuario"]

    # =========================
    # 📦 BASE POR NEGOCIO
    # =========================
    if tipo_negocio in (0, 2, 3):
        base = "facturacion"
    elif tipo_negocio == 4:
        base = "documentos"
    elif tipo_negocio == 5:
        base = "arrendamiento"
    elif tipo_negocio == 6:
        base = "parquimetros"
    elif tipo_negocio == 7:
        base = "productos"
    else:
        base = "facturacion"

    # =========================
    # 👤 PERFIL USUARIO
    # =========================
    if tipo_usuario == 1:
        perfil = "bmi"
    else:
        perfil = "home"

    # =========================
    # 📱 TIPO LOGIN
    # =========================
    if login_type == "APP":
        return None  # app no usa redirect

    if login_type == "POS":
        return f"{base}"  # directo al módulo

    # WEB
    return f"{perfil}/{base}"

# =========================
# 🔐 HELPERS
# =========================

def generar_token():
    return hashlib.sha256(f"{uuid.uuid4()}-{time.time()}".encode()).hexdigest()


def validar_password(input_pass: str, db_pass: str):
    legacy = hashlib.md5(
        hashlib.sha1(input_pass.encode()).digest()
    ).hexdigest()

    print(input_pass,legacy,db_pass)

    if db_pass == legacy:
        return True

    if db_pass == input_pass:
        return True

    return False


def get_primary_sucursal(idsucursal: str):
    if not idsucursal:
        return None

    try:
        return int(idsucursal.split(",")[0])
    except:
        return None


def validar_horario(l1, l2, tipo):
    if tipo == 1:
        return True

    if not l1 or not l2:
        return True

    now = datetime.now().time()
    return l1 <= now <= l2


# =========================
# 🚀 LOGIN WEB
# =========================

@router.post("/login")
def login(data: dict, response: Response, request: Request):

    user = data.get("usr")
    password = data.get("pss")
    device_id = data.get("device_id") or str(uuid.uuid4())

    if not user or not password:
        raise HTTPException(422, "Usuario y contraseña requeridos")

    # =====================================
    # 🔍 DETECTAR TIPO CLIENTE
    # =====================================
    client_type = request.headers.get("X-Client-Type")

    if not client_type:
        ua = request.headers.get("user-agent", "").lower()

        if "flet" in ua:
            client_type = "APP"
        elif "postman" in ua or "python" in ua:
            client_type = "POS"
        else:
            client_type = "WEB"

    # normalizar
    client_type = client_type.upper()

    if client_type not in ["WEB", "APP", "POS"]:
        client_type = "WEB"

    # =========================
    # 🔎 USUARIO
    # =========================
    row = ejecutar_api(f"""
        SELECT id, user, nombre, clave, idTipoUsuario,
               idsucursal, limite1, limite2
        FROM usuarios
        WHERE user = %s
        and clave = md5(aes_encrypt("{password}",'lt6969'))
        LIMIT 1
    """, (user,),"one",response)

    if not row:
        raise HTTPException(401, "Usuario o contraseña incorrectos")

    #if not validar_password(password, row["clave"]):
    #    raise HTTPException(401, "Usuario o contraseña incorrectos")

    # =========================
    # ⏰ HORARIO
    # =========================
    if not validar_horario(row["limite1"], row["limite2"], row["idTipoUsuario"]):
        raise HTTPException(403, "Ingreso fuera de horario")

    # =========================
    # 🏢 SUCURSAL
    # =========================
    sucursal_id = get_primary_sucursal(row["idsucursal"])
    sucursal_id = 0 if sucursal_id == -1 else sucursal_id
    
    if sucursal_id < 0 or sucursal_id == '':
        raise HTTPException(403, "Usuario sin sucursal")

    sucursal = ejecutar_api("""
        SELECT id, nombre, idtiponegocio
        FROM sucursales
        WHERE id = %s
    """, (sucursal_id,),"one",response)

    if not sucursal:
        raise HTTPException(403, "Sucursal inválida")

    # =========================
    # 🌐 INFO CLIENTE
    # =========================
    ip = request.client.host
    ua = request.headers.get("user-agent", "")

    # =========================
    # 🔌 AUTH DEVICE (UPSERT)
    # =========================
    ejecutar_api("""
        INSERT INTO auth_devices (
            user_id, device_id, tipo, nombre,
            ip, user_agent, last_login
        )
        VALUES (%s,%s,'web','Browser',%s,%s,NOW())
        ON DUPLICATE KEY UPDATE
            last_login = NOW(),
            ip = VALUES(ip),
            user_agent = VALUES(user_agent)
    """, (row["id"], device_id, ip, ua),"none",response)

    # =====================================
    # ⏳ EXPIRACIÓN SEGÚN TIPO
    # =====================================
    if client_type == "WEB":
        expires_sql = "DATE_ADD(NOW(), INTERVAL 2 HOUR)"
    elif client_type == "APP":
        expires_sql = "NULL"  # sin expiración
    elif client_type == "POS":
        expires_sql = "NULL"  # controlado por LAN
    else:
        expires_sql = "DATE_ADD(NOW(), INTERVAL 2 HOUR)"

    # =========================
    # 🔐 TOKENS
    # =========================
    token = generar_token()
    refresh = generar_token()

    expires = datetime.now() + timedelta(minutes=60)
    refresh_expires = datetime.now() + timedelta(days=1)

    # =========================
    # 🧠 CONTROL SESIONES (max 3)
    # =========================
    ejecutar_api("""
        DELETE FROM auth_tokens
        WHERE user_id = %s
        ORDER BY last_activity ASC
        LIMIT 1
    """, (row["id"],),"none",response)

    # =========================
    # 💾 AUTH TOKEN
    # =========================
    ejecutar_api(f"""
        INSERT INTO auth_tokens (
            user_id, sucursal_id, device_id,
            token, refresh_token,
            expires_at, refresh_expires_at,
            last_activity
        )
        VALUES (%s,%s,%s,%s,%s,{expires_sql},%s,NOW())
    """, (
        row["id"],
        sucursal_id,
        device_id,
        token,
        refresh,
        refresh_expires
    ),"none",response)

    # =========================
    # 🧾 AUTH SESSION
    # =========================
    ejecutar_api("""
        INSERT INTO auth_sessions (
            user_id, sucursal_id, device_id,
            token, ip_address, user_agent,
            login_at, last_activity, is_active
        )
        VALUES (%s,%s,%s,%s,%s,%s,NOW(),NOW(),1)
    """, (
        row["id"],
        sucursal_id,
        device_id,
        token,
        ip,
        ua
    ),"none",response)

    # =========================
    # 🍪 COOKIE
    # =========================
    is_https = request.url.scheme == "https"

    response.set_cookie(
        key="apsy_token",
        value=token,
        httponly=is_https,
        secure=True,
        samesite="Lax"
    )

    # =========================
    #  REDIRECT
    # =========================

    redirect = 'facturacion'

    # =========================
    # 🎯 RESPONSE
    # =========================
    return {
        "ok": True,
        "redirect": redirect,
        "data": {
            "user_id":          row["id"],
            "user_name":        row["nombre"],
            "tipo_usuario":     row["idTipoUsuario"],
            "sucursal_id":      sucursal["id"],
            "sucursal_nombre":  sucursal["nombre"],
        }
    }

@router.get("/me")
def me(request: Request):

    # 🔴 si no pasó middleware, no hay sesión
    if not hasattr(request.state, "user_id"):
        return JSONResponse(
            status_code=401,
            content={"ok": 0, "msg": "No autenticado"}
        )

    return {
        "ok": 1,
        "data": {
            "user_id": request.state.user_id,
            "user_nombre": request.state.user_nombre,
            "sucursal_id": request.state.sucursal_id,
            "sucursal_nombre": request.state.sucursal_nombre,
            "device_id": request.state.device_id,
            "business": request.state.tipo_negocio
        }
    }

@router.post("/logout")
def logout(request: Request, response: Response):

    token = request.cookies.get("apsy_token")

    if token:
        db("DELETE FROM auth_tokens WHERE token = %s", (token,))

    response.delete_cookie("apsy_token")

    return {"ok": 1}