from modules.db import get_connection

def guardar_formulario(codigo, data):
    db = get_connection()

    # 🔹 1. Buscar configuración
    sql = "SELECT tabla FROM formularios.config WHERE codigo = %s LIMIT 1"
    result = db.fetch_one(sql, (codigo,))

    if not result:
        return {"success": 0, "msj": "Formulario no existe"}

    tabla = result["tabla"]

    # 🔒 Seguridad básica
    if not tabla.isidentifier():
        return {"success": 0, "msj": "Tabla inválida"}

    # 🔹 2. Flatten (checkboxes, arrays)
    data = flatten_data(data)

    # 🔹 3. Construir INSERT dinámico
    campos = []
    valores = []
    params = []

    for key, val in data.items():
        if val is None or val == "":
            continue

        campos.append(f"`{key}`")
        valores.append("%s")
        params.append(val)

    if not campos:
        return {"success": 0, "msj": "Sin datos"}

    sql_insert = f"""
        INSERT INTO {tabla} ({",".join(campos)})
        VALUES ({",".join(valores)})
    """

    try:
        db.execute(sql_insert, params)
        return {"success": 1}
    except Exception as e:
        return {"success": 0, "msj": str(e)}