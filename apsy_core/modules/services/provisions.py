import secrets
import time
from modules.db import ejecutar_api

# cache temporal de init
INSTALL_SESSIONS = {}

def create_session(fingerprint, hostname, ip, token, expires):

    ejecutar_api("""
            INSERT INTO crm_provision_sessions (
                fingerprint,
                hostname,
                ip,
                token,
                expires_at
            ) VALUES (%s,%s,%s,%s,%s)
        """, (fingerprint, hostname, ip, token, expires),'None')

def validate_init_token(token, fingerprint):

    session = INSTALL_SESSIONS.get(token)

    if not session:
        return False

    if session["exp"] < time.time():
        return False

    if session["fingerprint"] != fingerprint:
        return False

    return session


def get_ws_settings():

    return {
        "sync_interval": 30,
        "batch_size": 200,
        "retry": 3,
        "offline": True
    }


def register_terminal(empresa_id, data):

    return ejecutar_api("""
        INSERT INTO crm_terminales (
            empresa_id,
            hostname,
            ip,
            device_uid,
            tipo,
            version
        ) VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        empresa_id,
        data["hostname"],
        data["ip"],
        data["fingerprint"],
        "pos",
        data.get("version", "1.0.0")
    ),"none")


def build_crm_initial(empresa_id):

    return {
        "tenant_created": True,
        "default_plan": "trial",
        "status": "active"
    }