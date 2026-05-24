from fastapi import APIRouter, Request
from modules.framework.dispatcher import get_function
from modules.db import ejecutar_api
from functools import partial

router = APIRouter()

def tiene_permiso(db, user_id, fn):
    denied = db("""
        SELECT 1
        FROM bkl_permisos_core
        WHERE user_id = %s AND fn = %s
    """, (user_id, fn), "one")

    return denied is None


def is_debug_allowed(user_id):
    # 👉 aquí luego validás rol
    return True


@router.post("/core")
def core_api(request: Request, data: dict):

    debug_mode = data.get("_debug", 0) == 1
    debug_trace = []

    user_id = request.state.user_id

    try:
        # 📦 DATA
        fn = data.get("fn")
        params = data.get("params", {})

        if not fn:
            return {"error": "fn requerido"}

        debug_trace.append(f"FN: {fn}")

        # 🔐 PERMISOS
        #debug_trace.append("Validando permisos")
        #if not tiene_permiso(ejecutar_api, user_id, fn):
        #    return {"error": "Sin permisos"}

        # ⚙️ DISPATCHER
        debug_trace.append("Resolviendo función")
        func, error = get_function(fn,request)

        if error:
            return {"error": error}

        debug_trace.append(f"Ejecutando función/SP: {func}")

        db = partial(
            ejecutar_api,
            request=request
        )
        # 🚀 EJECUCIÓN
        
        result = func(db, params)

        response = {
            "ok": True,
            "data": result
        }

        # 🧠 DEBUG CONTROLADO
        if debug_mode and is_debug_allowed(user_id):
            response["_debug"] = debug_trace

        return response

    except Exception as e:
        response = {"error": str(e)}

        if debug_mode:
            response["_debug"] = debug_trace

        return response