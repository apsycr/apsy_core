from fastapi import Request
import json
import os
import re

BASE_PATH = "static/forms"


def normalizar(nombre):
    nombre = nombre.lower().replace(" ", "_")
    return re.sub(r'[^a-z0-9_]', '', nombre)


def mapear_tipo(tipo):
    return {
        "text": "VARCHAR(255)",
        "textarea": "TEXT",
        "number": "DECIMAL(10,2)",
        "radio": "INT",
        "checkbox": "TINYINT(1)",
        "select": "VARCHAR(100)",
        "signature": "LONGTEXT"
    }.get(tipo, "TEXT")


def crear_tabla(db, form_id, title, fields):

    tabla = f"formularios_{form_id}_{normalizar(title)}"

    cols = [
        "id INT AUTO_INCREMENT PRIMARY KEY",
        "fecha DATETIME DEFAULT CURRENT_TIMESTAMP"
    ]

    for f in fields:
        if f.get("persist", True):
            cols.append(f"{f['name']} {mapear_tipo(f['type'])}")

    sql = f"CREATE TABLE {tabla} ({', '.join(cols)})"
    db(sql, (), "none")

    return tabla


# =========================
# 🔹 SAVE
# =========================
def save(db, p):

    schema = p.get("schema")

    if not schema:
        raise Exception("Schema requerido")

    title = schema.get("title", "formulario")

    db("""
        INSERT INTO formularios.config (name, schema_json, idsucursal)
        VALUES (%s, %s, %s)
    """, (title, json.dumps(schema), request.state.sucursal_id), "none")

    row = db("SELECT LAST_INSERT_ID() id", (), "one")
    form_id = row["id"]

    tabla = crear_tabla(db, form_id, title, schema.get("fields", []))

    db("""
        UPDATE formularios.config
        SET table_name = %s
        WHERE id = %s
    """, (tabla, form_id), "none")

    html = generar_html(form_id, title)

    os.makedirs(BASE_PATH, exist_ok=True)

    with open(f"{BASE_PATH}/{form_id}.html", "w", encoding="utf-8") as f:
        f.write(html)

    return {"id": form_id}


# =========================
# 🔹 GET
# =========================
def get(db, p):

    row = db("""
        SELECT schema_json
        FROM formularios.config
        WHERE id = %s
    """, (p["id"],), "one")

    if not row:
        raise Exception("No existe formulario")

    return json.loads(row["schema_json"])


# =========================
# 🔹 INSERT DATA
# =========================
def insert(db, p):

    form_id = p["form_id"]
    data    = p["data"]

    row = db("""
        SELECT table_name
        FROM formularios.config
        WHERE id = %s
    """, (form_id,), "one")

    tabla = row["tabla"]

    campos = list(data.keys())
    valores = list(data.values())

    cols = ", ".join(campos)
    vals = ", ".join(["%s"] * len(valores))

    sql = f"INSERT INTO formularios.{tabla} ({cols}) VALUES ({vals})"

    db(sql, tuple(valores), "none")

    return {"ok": True}


# =========================
# 🔹 HTML
# =========================
def generar_html(form_id, title):

    return f"""
<html>
<head>
<link rel="stylesheet" href="/assets/css/materialize.min.css">
<script src="/assets/js/jquery.js"></script>
<script src="/assets/js/asgard.js"></script>
<script src="/assets/js/forms.js"></script>
</head>

<body>

<div class="container">
    <h5>{title}</h5>
    <div id="app"></div>
    <button onclick="guardar()" class="btn">Guardar</button>
</div>

<script>

const FORM_ID = {form_id}

function load(){{
    asgard.fetch({{
        fn: "forms.get",
        params: {{id: FORM_ID}}
    }}).then(r=>{{
        if(r.ok) asgard.forms.render(r.data, "#app")
    }})
}}

function guardar(){{
    let data = asgard.forms.getData("#app")

    asgard.fetch({{
        fn: "forms.insert",
        params: {{
            form_id: FORM_ID,
            data: data
        }}
    }})
}}

document.addEventListener("DOMContentLoaded", load)

</script>

</body>
</html>
"""


FUNCTIONS = {
    "save": save,
    "get": get,
    "insert": insert
}