from modules.db import ejecutar_api


# =========================
# 🔎 OBTENER PARÁMETROS DESDE core_fields
# =========================
def get_sp_params(fn,request):
    """
    Obtiene el orden de parámetros desde core_fields
    basado en fn (mant.incapacidades)
    """

    fields = ejecutar_api("""
        SELECT column_name
        FROM core_fields
        WHERE fn = ?
        ORDER BY id
    """, (fn,), "all",request)

    if not fields:
        raise Exception(f"No hay definición de campos para '{fn}'")

    return [f["column_name"] for f in fields]


# =========================
# ⚙️ EJECUTAR SP DINÁMICO
# =========================
def ejecutar_sp(db, sp_name, input_params, fn=None):
    """
    db: función ejecutar(sql, params, fetch)
    sp_name: nombre real del SP (sp_mant_incapacidades)
    input_params: dict enviado desde frontend
    fn: opcional (para validar orden desde core_fields)
    """

    # =====================================
    # FLAGS INTERNAS
    # =====================================

    use_multi = input_params.pop(
        "_pagination",
        False
    )

    # =========================
    # 🔐 ORDEN DE PARÁMETROS
    # =========================
    if fn:
        param_names = get_sp_params(fn)
    else:
        # fallback: usar orden del dict (menos seguro)
        param_names = list(input_params.keys())

    args = []

    for campo in param_names:
        if campo.startswith("_"):
            continue  # ignorar internos

        if campo not in input_params:
            raise Exception(f"Falta parámetro '{campo}'")

        args.append(input_params[campo])

    # =========================
    # 🧩 ARMAR SQL
    # =========================
    placeholders = ",".join(["?"] * len(args))
    sql = f"CALL {sp_name}({placeholders})"

    # =========================
    # 🚀 EJECUCIÓN
    # =========================
    fetch = "multi" if use_multi else "all"
    result = db(
        sql,
        tuple(args),
        fetch
    )

    if use_multi:

        return {
            "pagination": result[0][0] if result[0] else {},
            "rows": result[1] if len(result) > 1 else []
        }

    return result