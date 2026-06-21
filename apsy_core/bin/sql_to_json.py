import json
from pathlib import Path
import re

def normalize_sql(sql):

    sql = re.sub(
        r"DELIMITER\s+\$\$",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = re.sub(
        r"DELIMITER\s+;",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = sql.replace("$$", ";")

    return sql.strip()

def sql_to_json(
    sql_file,
    json_file,
    version="1.0.0",
    description=""
):

    sql_path = Path(sql_file)

    sql = normalize_sql(sql)

    sql_text = sql_path.read_text(
        encoding="utf-8"
    )

    statements = []

    current = []

    for line in sql_text.splitlines():

        current.append(line)

        if ";" in line:

            stmt = "\n".join(current).strip()

            if stmt:

                statements.append(stmt)

            current = []

    if current:

        stmt = "\n".join(current).strip()

        if stmt:

            statements.append(stmt)

    data = {

        "version": version,
        "description": description,
        "sql": statements

    }

    Path(json_file).write_text(

        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        ),

        encoding="utf-8"
    )

    print(
        f"Generado: {json_file}"
    )