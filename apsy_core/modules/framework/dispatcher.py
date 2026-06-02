import importlib
from modules.framework.sp_registry import ejecutar_sp
from modules.framework.grid_service  import get_grid
from modules.framework.query_service  import ejecutar_query
from modules.db import ejecutar_api

MODULE_CACHE = {}
# =========================
# 🔹 HELPERS BASE
# =========================

def ejecutar_crud(db, tabla, params):
    accion = params.get("_accion")

    if not accion:
        raise Exception("Acción requerida (_accion)")

    # 🔹 INSERT
    if accion == 1:
        campos = [k for k in params.keys() if not k.startswith("_")]
        valores = [params[k] for k in campos]

        cols = ", ".join(campos)
        vals = ", ".join(["?"] * len(valores))

        sql = f"INSERT INTO {tabla} ({cols}) VALUES ({vals})"
        return db(sql, tuple(valores), "none")

    # 🔹 UPDATE
    elif accion == 2:
        if "id" not in params:
            raise Exception("ID requerido para update")

        campos = [k for k in params.keys() if k not in ("id", "_accion")]

        sets = ", ".join([f"{k}=?" for k in campos])
        valores = [params[k] for k in campos]

        sql = f"UPDATE {tabla} SET {sets} WHERE id=?"
        valores.append(params["id"])

        return db(sql, tuple(valores), "none")

    # 🔹 DELETE
    elif accion == 3:
        if "id" not in params:
            raise Exception("ID requerido para delete")

        sql = f"DELETE FROM {tabla} WHERE id=?"
        return db(sql, (params["id"],), "none")

    else:
        raise Exception(f"Acción no soportada: {accion}")


# =========================
# 🔹 CORE FUNCTIONS
# =========================

def get_core_function(funcion):

    # 🔹 STRUCT (reemplazo de 482)
    if funcion == "struct":
        return lambda db, p: db(
            "CALL sp_structure(?)",
            (p,),
            "all"
        )

    # 🔹 GRID STRUCT
    if funcion == "grid":
        return lambda db, p: get_grid(db, p)

    # 🔹 SP DIRECTO CONTROLADO

    if funcion.startswith("sp_"):
        return lambda db, p: ejecutar_sp(db, funcion, p)

    raise Exception(f"Función core no soportada: {funcion}")

# =========================
# 🔹 DB PROCESOS (core_procesos)
# =========================

def get_db_proceso(fn,request):

    proc = ejecutar_api("""
        SELECT tipo, referencia
        FROM core_procesos
        WHERE fn = ?
          AND activo = 1
        LIMIT 1
    """, (fn,), "one",request)

    return proc


# =========================
# 🔹 DISPATCHER PRINCIPAL
# =========================

def get_function(fn_path: str,request):

    try:
        modulo, funcion = fn_path.split(".", 1)
    except ValueError:
        return None, "Formato inválido (modulo.funcion)"

    # =========================
    # 🔥 CORE
    # =========================
    if modulo == "core":
        try:
            fn = get_core_function(funcion)
            return fn, None
        except Exception as e:
            return None, str(e)

    # =========================
    # 🔥 MÓDULOS PYTHON (PRIORIDAD + CACHE)
    # =========================
    mod = MODULE_CACHE.get(modulo)

    if mod is None:

        try:
            mod = importlib.import_module(f"modules.framework.{modulo}")
            MODULE_CACHE[modulo] = mod

        except ModuleNotFoundError:
            MODULE_CACHE[modulo] = False
            mod = False

    # 👉 si existe módulo
    if mod:
        functions = getattr(mod, "FUNCTIONS", {})

        if funcion in functions:
            entry = functions[funcion]

            if isinstance(entry, dict):
                return entry["fn"], None

            return entry, None

    # =========================
    # 🔥 DB (fallback)
    # =========================
    proc = get_db_proceso(fn_path,request)
    
    if proc:
        tipo = proc["tipo"]
        ref  = proc["referencia"]

        if tipo == "sp":
            return lambda db, p: ejecutar_sp(db, ref, p), None

        elif tipo == "query":
            return lambda db, p: ejecutar_query(db, ref, p, request), None

        elif tipo == "crud":
            return lambda db, p: ejecutar_crud(db, ref, p), None

        else:
            return None, f"Tipo no soportado: {tipo}"

    return None, f"Función '{fn_path}' no encontrada"