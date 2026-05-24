import json


def get_grid(db, params):

    fn = params.get("fn")

    if not fn:

        return {

            "ok": False,
            "error": "fn requerido"

        }

    # =====================================
    # GRID CONFIG
    # =====================================

    rows = db("""

        SELECT

            column_name,
            label,
            orden,
            align

        FROM core_grids

        WHERE idtable = ?

        ORDER BY orden

    """, (fn,), 'all')

    # =====================================
    # BUILD COLUMNS
    # =====================================

    columns = []

    for r in rows:

        columns.append({

            "field": r["column_name"],
            "label": r["label"],
            "align": r["align"]

        })

    # =====================================
    # FILTERS
    # =====================================

    filtro_row = db("""

        SELECT

            json

        FROM core_filters

        WHERE core_reports = ?

        LIMIT 1

    """, (fn,), 'one')

    filtros = {}

    if filtro_row:

        try:

            filtros = json.loads(
                filtro_row["json"] or "{}"
            )

        except Exception:

            filtros = {}

    # =====================================
    # RESPONSE
    # =====================================

    return {

        "ok": True,
        "columns": columns,
        "filtros": filtros

    }