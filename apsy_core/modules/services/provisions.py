import secrets
import time
from datetime import datetime
import json
from pathlib import Path

from modules.db import ejecutar_api

def normalize_version(v):

    return tuple(
        int(x)
        for x in str(v).split(".")
    )

def get_database_path():

    paths = [

        Path("/opt/apsy/databases"),
        Path("C:/apsy/docker_dev/databases")

    ]

    for path in paths:

        if path.exists():

            return path

    raise Exception(
        "Database repository not found"
    )


DATABASES_PATH = get_database_path()


def get_install_credentials():

    return {

        "db": {

            "host": "mariadb",
            "user": "ws_user",
            "database": "ws_local",
            "port": 3306,
            "password_plain": "apsyws20"

        },

        "db_api": {

            "host": "mariadb",
            "user": "itech01",
            "database": "production",
            "port": 3306,
            "password_plain": "Login2Help"

        }

    }


def get_latest_version():

    latest = normalize_version("0.0.0.0")

    updates_dir = DATABASES_PATH / "updates"

    if not updates_dir.exists():

        return "0.0.0.0"

    for file in updates_dir.glob("*.json"):

        try:

            data = json.loads(
                file.read_text(
                    encoding="utf-8"
                )
            )

            version = normalize_version(
                str(data["version"])
            )

            if version > latest:

                latest = version

        except Exception:

            continue

    return str(latest)


def get_updates(client_version):

    updates = []

    current = normalize_version(
        str(client_version)
    )

    updates_dir = DATABASES_PATH / "updates"

    if not updates_dir.exists():

        return []

    for file in sorted(
        updates_dir.glob("*.json")
    ):

        try:

            data = json.loads(
                file.read_text(
                    encoding="utf-8"
                )
            )

            version = normalize_version(
                str(data["version"])
            )

            if version > current:

                updates.append(data)

        except Exception:

            continue

    return updates

def create_session(fingerprint, hostname, ip, token, expires):

    ejecutar_api("""
            INSERT INTO crm_provision_sessions (
                fingerprint,
                hostname,
                ip,
                token,
                expires_at
            ) VALUES (%s,%s,%s,%s,%s)
        """, (fingerprint, hostname, ip, token, expires),'none')

def validate_token_from_db(token):

    sql = """
        SELECT
            id,
            fingerprint,
            hostname,
            expires_at,
            status
        FROM crm_provision_sessions
        WHERE token=%s
        LIMIT 1
    """

    row = ejecutar_api(sql, (token,),'one')

    if not row:
        return None

    if row["status"] != "active":
        return None

    if datetime.now() > row["expires_at"]:
        return None

    return row

def detect_onboarding_mode(fingerprint, cedula=None):

    sql = """
        SELECT
            id,
            empresa_id,
            sucursal_id
        FROM crm_terminales
        WHERE device_uid=%s
        LIMIT 1
    """

    terminal = ejecutar_api(sql, (fingerprint,),'one')

    if terminal:

        return {
            "mode": "existing_terminal",
            "empresa_id": terminal["empresa_id"],
            "sucursal_id": terminal["sucursal_id"]
        }

    if cedula:

        sql = """
            SELECT id
            FROM crm_tenants
            WHERE cedula=%s
            LIMIT 1
        """

        tenant = ejecutar_api(sql, (cedula,),'one')

        if tenant:

            return {
                "mode": "new_branch",
                "empresa_id": tenant["id"]
            }

    return {
        "mode": "new_customer"
    }

def get_install_credentials():

    return {

        "db": {
            "host": "mariadb",
            "user": "ws_user",
            "database": "ws_local",
            "port": 3306,
            "password_plain": "apsyws20"
        },

        "db_api": {
            "host": "mariadb",
            "user": "itech01",
            "database": "production",
            "port": 3306,
            "password_plain": "Login2Help"
        }

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

def create_tenant_auto(data):

    sql = """
        INSERT INTO crm_tenants(
            nombre,
            cedula,
            telefono,
            email,
            estado
        )
        VALUES(
            %s,%s,%s,%s,'trial'
        )
    """

    ejecutar_api(sql, (
        data["nombre"],
        data["cedula"],
        data["telefono"],
        data["email"]
    ),'none')

    tenant_id = db.lastrowid()

    ejecutar_api(
        """
        INSERT INTO crm_sucursales(
            empresa_id,
            nombre
        )
        VALUES(%s,'Principal')
        """,
        (tenant_id,),'none'
    )

    return tenant_id

def assign_trial_plan(tenant_id):

    plan = ejecutar_api("""
        SELECT id
        FROM crm_planes
        WHERE nombre='TRIAL'
        LIMIT 1
    """,(),'one')

    if not plan:
        raise Exception("Plan TRIAL no existe")

    ejecutar_api("""
        INSERT INTO crm_contratos(
            tenant_id,
            plan_id,
            estado,
            fecha_inicio
        )
        VALUES(
            %s,%s,
            'trial',
            CURDATE()
        )
    """, (
        tenant_id,
        plan["id"]
    ), 'none')

    return plan["id"]