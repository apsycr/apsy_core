import json
import re

from modules.db import ejecutar_api


# =========================================
# 🔎 GET QUERY
# =========================================

def get_query(nombre,request=None):

    row = ejecutar_api("""

        SELECT

            nombre,
            sql_query,
            json_query

        FROM core_queries

        WHERE nombre = ?

    """, (

        nombre,

    ), "one", request)

    if not row:

        raise Exception(
            f"Query '{nombre}' no existe"
        )

    return row


# =========================================
# 🔧 SQL -> PARAMS COUNT
# =========================================

def count_sql_params(sql):
    return len(
        re.findall(r'\?', sql)
    )


# =========================================
# 🧩 JSON -> SQL
# =========================================

def json_to_sql(query_json):

    # =========================
    # SELECT
    # =========================

    select = query_json.get(
        "select",
        ["*"]
    )

    sql = "SELECT\\n    "

    sql += ",\\n    ".join(select)

    # =========================
    # FROM
    # =========================

    from_table = query_json.get("from")

    if not from_table:

        raise Exception(
            "JSON query requiere 'from'"
        )

    sql += f"\\nFROM {from_table}"

    # =========================
    # JOINS
    # =========================

    joins = query_json.get(
        "joins",
        []
    )

    for join in joins:

        join_type = join.get(
            "type",
            "LEFT"
        )

        sql += f'''

{join_type} JOIN {join["table"]}
    ON {join["on"]}

'''

    # =========================
    # WHERE
    # =========================

    where = query_json.get(
        "where",
        []
    )

    if where:

        sql += "\\nWHERE\\n"

        conditions = []

        for cond in where:

            field = cond["field"]

            op = cond.get(
                "op",
                "="
            )

            value = cond.get(
                "value",
                "?"
            )

            conditions.append(
                f"{field} {op} {value}"
            )

        sql += "\\nAND ".join(conditions)

    # =========================
    # GROUP
    # =========================

    group = query_json.get(
        "group_by",
        []
    )

    if group:

        sql += "\\nGROUP BY\\n    "

        sql += ", ".join(group)

    # =========================
    # ORDER
    # =========================

    order = query_json.get(
        "order_by",
        []
    )

    if order:

        sql += "\\nORDER BY\\n"

        rows = []

        for item in order:

            rows.append(

                f'''

{item["field"]} {item.get("dir", "ASC")}

'''.strip()

            )

        sql += ", ".join(rows)

    # =========================
    # LIMIT
    # =========================

    limit = query_json.get("limit")

    if limit:

        sql += f"\\nLIMIT {limit}"

    return sql.strip()


# =========================================
# 🧩 SQL -> JSON
# =========================================

def sql_to_json(sql):

    result = {

        "select": [],
        "from": None,
        "where": [],
        "order_by": []

    }

    sql_clean = (
        sql
        .replace("\\n", " ")
        .replace("\\t", " ")
    )

    # =========================
    # SELECT
    # =========================

    m = re.search(

        r"SELECT\\s+(.*?)\\s+FROM",

        sql_clean,

        re.I

    )

    if m:

        result["select"] = [

            x.strip()

            for x in m.group(1).split(",")

        ]

    # =========================
    # FROM
    # =========================

    m = re.search(

        r"FROM\\s+([a-zA-Z0-9_]+)",

        sql_clean,

        re.I

    )

    if m:

        result["from"] = m.group(1)

    # =========================
    # WHERE
    # =========================

    m = re.search(

        r"WHERE\\s+(.*?)(ORDER BY|GROUP BY|LIMIT|$)",

        sql_clean,

        re.I

    )

    if m:

        where_block = m.group(1)

        parts = re.split(

            r"\\s+AND\\s+",

            where_block,

            flags=re.I

        )

        for p in parts:

            m2 = re.match(

                r"(.+?)\\s*(=|>|<|>=|<=|LIKE)\\s*(.+)",

                p.strip(),

                re.I

            )

            if m2:

                result["where"].append({

                    "field":
                        m2.group(1).strip(),

                    "op":
                        m2.group(2).strip(),

                    "value":
                        m2.group(3).strip()

                })

    # =========================
    # ORDER
    # =========================

    m = re.search(

        r"ORDER BY\\s+(.*?)(LIMIT|$)",

        sql_clean,

        re.I

    )

    if m:

        items = m.group(1).split(",")

        for item in items:

            p = item.strip().split()

            result["order_by"].append({

                "field": p[0],

                "dir":
                    p[1]
                    if len(p) > 1
                    else "ASC"

            })

    return result


# =========================================
# ⚙️ EJECUTAR QUERY
# =========================================

def ejecutar_query(

        db,
        query_name,
        input_params=None,
        request=None

):

    # =========================
    # 🔎 QUERY
    # =========================

    row = get_query(query_name,request)

    sql_query = row.get("sql_query")

    json_query = row.get("json_query")

    # =========================
    # 🧩 SQL
    # =========================

    if sql_query:

        sql = sql_query

    elif json_query:

        if isinstance(json_query, str):

            query_json = json.loads(
                json_query
            )

        else:

            query_json = json_query

        sql = json_to_sql(query_json)

    else:

        raise Exception(
            f"Query '{query_name}' vacía"
        )

    # =========================
    # 🔐 PARAMS
    # =========================

    if input_params is None:
        input_params = []

    sql, input_params = apply_special_params(
        sql,
        input_params
    )

    expected_params = count_sql_params(sql)

    if isinstance(input_params, dict):

        input_params = list(
            input_params.values()
        )

    if len(input_params) != expected_params:

        raise Exception(

            f"""

Parámetros incompatibles

SQL espera:
{expected_params}

Recibidos:
{len(input_params)}

"""

        )

    # =========================
    # 🚀 EXEC
    # =========================

    return ejecutar_api(

        sql,

        tuple(input_params),

        "all",

        request

    )

def apply_special_params(sql, params):

    if not isinstance(params, dict):
        return sql, params

    # =========================
    # @@search
    # =========================

    if '@@search' in sql:

        search = (
            params.get('search', '')
            .strip()
        )

        sql = sql.replace(
            '@@search',
            '?'
        )

        params['search'] = (
            f'%{search}%'
        )

    return sql, params