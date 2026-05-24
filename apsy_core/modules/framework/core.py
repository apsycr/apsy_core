from modules.framework.sp_registry import ejecutar_sp


# =========================
# 🔹 STRUCT (core_init)
# =========================
def core_struct(db, params):
    """
    params = table_id
    """
    return db(
        "CALL sp_structure(?)",
        (params,),
        "all"
    )


# =========================
# 🔹 GRID CONFIG
# =========================
def core_grid(db, params):

    fn = params.get("fn")

    if not fn:
        raise Exception("fn requerido")

    proceso = db("""
        SELECT id
        FROM core_procesos
        WHERE fn = %s
        LIMIT 1
    """, (fn,), "one")

    if not proceso:
        raise Exception(f"Proceso '{fn}' no existe")

    table_id = proceso["id"]

    columns = db("""
        SELECT field, label, align, tipo
        FROM core_columns
        WHERE table_id = %s
        ORDER BY orden
    """, (table_id,), "all")

    filtros = {}

    fields = db("""
        SELECT column_name, default_value
        FROM core_fields
        WHERE table_id = %s
    """, (table_id,), "all")

    for f in fields:
        filtros[f["column_name"]] = f["default_value"]

    return {
        "columns": columns,
        "filtros": filtros
    }


# =========================
# 🔹 SP DINÁMICO
# =========================
def core_sp(db, sp_name, params):
    return ejecutar_sp(db, sp_name, params)


# =========================
# 🔹 REGISTRO CENTRAL
# =========================
FUNCTIONS = {
    "struct": core_struct,
    "grid": core_grid,
}