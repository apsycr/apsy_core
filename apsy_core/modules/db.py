import mariadb
import logging
from contextlib import contextmanager
from modules.config import load_config
from modules.security import decrypt_value
from datetime import datetime

_config = load_config()
logger = logging.getLogger("ws-server-local")

# =========================
# 🔌 CONEXIÓN
# =========================

pools = {}

def get_db_config(name="db"):
    """
    Retorna configuración de DB lista para usar en pool
    name: 'db' o 'db_api'
    """
    db_cfg = _config.get(name, {})

    password = None

    # 🔐 Prioridad 1: password encriptado
    if "password" in db_cfg:
        password = decrypt_value(db_cfg["password"])
    else:
        raise Exception(f"No password definido para {name}")
    
    return {
        "host": db_cfg.get("host", "localhost"),
        "user": db_cfg.get("user"),
        "password": password,
        "database": db_cfg.get("database"),
        "port": db_cfg.get("port", 3306),
    }

def init_pools():
    db = get_db_config("db")

    pools['db'] = mariadb.ConnectionPool(
        pool_name="pool_db",
        host=db['host'],
        user=db['user'],
        password=db['password'],
        database=db['database'],
        port=db['port'],
        pool_size=5
    )

    db_api = get_db_config("db_api")

    pools['db_api'] = mariadb.ConnectionPool(
        pool_name="pool_db_api",
        host=db_api['host'],
        user=db_api['user'],
        password=db_api['password'],
        database=db_api['database'],
        port=db_api['port'],
        pool_size=5
    )  

def get_connection(db='db'):
    return pools[db].get_connection()

# =========================
# CONSTRUCTOR SEGURO
# =========================

def build_safe_context(request=None):

    if not request:
        return {}

    return {
        '@@usr'         : request.state.user_id,
        '@@idsucursal'  : request.state.sucursal_id,
        '@@device'      : request.state.device_id,
        '@@sucursal'    : request.state.sucursal_nombre,
        '@@negocio'     : request.state.tipo_negocio,
        '@@now'         : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '@@today'       : datetime.now().strftime('%Y-%m-%d'),
        '@@year'        : datetime.now().year,
        '@@month'       : datetime.now().month
    }

def inject_safe_context(sql, params=None, request=None):

    if not request:
        return sql, params

    context = build_safe_context(request)

    # SQL
    for k,v in context.items():
        sql = sql.replace(k, str(v))

    # PARAMS
    params = inject_safe_params(params, context)

    return sql, params

def inject_safe_params(params, context):

    if params is None:
        return params

    if isinstance(params, (list, tuple)):

        return tuple(
            resolve_safe_value(v, context)
            for v in params
        )

    if isinstance(params, dict):

        return {
            k: resolve_safe_value(v, context)
            for k,v in params.items()
        }

    return params

def resolve_safe_value(value, context):

    if isinstance(value, str):

        if value in context:
            return context[value]

    return value

# =========================
# 🧾 CONTEXT MANAGER (opcional)
# =========================
@contextmanager
def get_db():
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        yield cur
        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"DB error: {e}")
        raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# =========================
# 🪵 LOG DE ERRORES
# =========================
def log_error(sql, error):
    try:
        conn = get_connection('db_api')
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO registrosql VALUES (NULL, NOW(), ?, ?)",
            (sql, str(error))
        )

        conn.commit()

    except Exception as e:
        logger.error(f"Error guardando log SQL: {e}")

    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass


# =========================
# 🚀 EJECUTOR PRINCIPAL
# =========================
def ejecutar_api(sql, params=None,fetch="one",request=None):
    sql, params = inject_safe_context(
        sql,
        params,
        request
    )
    
    return ejecutar(sql,params,fetch,'db_api')


def ejecutar(sql, params=None, fetch="one",db="db"):
    """
    fetch:
        - "one"  → un registro
        - "all"  → lista
        - "none" → solo ejecutar (INSERT/UPDATE)
    """

    conn = None
    cur = None

    try:
        conn = get_connection(db)
        cur = conn.cursor(dictionary=True)

        cur.execute(sql, params or ())
        
        # =========================
        # 📊 RESPUESTA
        # =========================
        if fetch == "one":
            result = cur.fetchone()
        elif fetch == "all":
            result = cur.fetchall()
        else:
            result = cur.rowcount
        
        # 🔥 LIMPIAR RESULTSETS SIEMPRE
        while cur.nextset():
            pass

        conn.commit()
        return result

    except mariadb.Error as e:
        errno = getattr(e, "errno", None)

        # 🔍 limpieza SQL si es SP
        sql_log = sql
        if sql.strip().lower().startswith("call"):
            sql_log = sql[:sql.find("(")]

        params_str = repr(params)

        # =========================
        # 🪵 LOG SOLO ERRORES REALES
        # =========================
        if errno not in (1644, 45000):
            log_error(sql_log + params_str, e)

        # =========================
        # 🎯 TRADUCCIÓN DE ERRORES
        # =========================
        if errno == 1062:
            msg = str(e)
            valor = msg[msg.find("'"):msg.find(" for")]
            raise Exception(f"Valor {valor} existente")

        elif errno == 1318:
            raise Exception(f"Parámetros incompatibles en SP ({sql_log})")

        elif errno == 1172:
            raise Exception(sql_log)

        elif errno in (1644, 45000):
            # SIGNAL desde SP
            raise Exception(str(e))

        else:
            raise Exception(f"Error del sistema ({e})")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# =========================
# ⚙️ CONTROL (CLAVE-VALOR)
# =========================
def get_control(clave):
    row = ejecutar(
        "SELECT valor FROM ws_control WHERE clave=%s",
        (clave,),
        "one"
    )
    return row["valor"] if row else None


def set_control(clave, valor):
    ejecutar("""
        INSERT INTO ws_control (clave, valor)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            valor=VALUES(valor),
            updated_at=CURRENT_TIMESTAMP
    """, (clave, valor), "none")