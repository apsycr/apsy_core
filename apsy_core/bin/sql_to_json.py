import json
import mariadb
import re
import sys

from pathlib import Path


DEFAULT_OUTPUT_DIR = Path(
    r"C:\apsy\docker_dev\databases"
)

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "Login2Help2020",
    "database": "ws_local"
}


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

    sql = sql.replace(
        "$$",
        ";"
    )

    return sql.strip()


def next_version(version):

    major, minor, patch = map(
        int,
        version.split(".")
    )

    patch += 1

    return (
        f"{major}.{minor}.{patch}"
    )


def get_db_version():

    conn = mariadb.connect(
        **DB_CONFIG
    )

    cur = conn.cursor()

    cur.execute("""
        SELECT version
        FROM ws_system
        WHERE componente='db'
    """)

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:

        return "1.0.0"

    return row[0]


def sql_to_json(
    sql_file,
    output_dir
):

    sql_path = Path(
        sql_file
    )

    if not sql_path.exists():

        raise FileNotFoundError(
            sql_path
        )

    current_version = (
        get_db_version()
    )

    new_version = (
        next_version(
            current_version
        )
    )

    sql_text = (
        sql_path.read_text(
            encoding="utf-8"
        )
    )

    sql_text = normalize_sql(
        sql_text
    )

    statements = []

    current = []

    for line in sql_text.splitlines():

        current.append(
            line
        )

        if ";" in line:

            stmt = "\n".join(
                current
            ).strip()

            if stmt:

                statements.append(
                    stmt
                )

            current = []

    if current:

        stmt = "\n".join(
            current
        ).strip()

        if stmt:

            statements.append(
                stmt
            )

    output_dir = Path(
        output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    description = (
        sql_path.stem.lower()
        .replace(" ", "_")
    )

    json_file = (
        output_dir /
        f"{new_version}_{description}.json"
    )

    data = {

        "component": "db",

        "version": new_version,

        "description": description,

        "sql": statements

    }

    json_file.write_text(

        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        ),

        encoding="utf-8"
    )

    print()
    print(
        f"Versión actual : {current_version}"
    )
    print(
        f"Nueva versión  : {new_version}"
    )
    print(
        f"Archivo generado: {json_file}"
    )
    print()


def main():

    if len(sys.argv) < 2:

        print(
            "\nUso:"
        )

        print(
            "py sql_to_json.py archivo.sql"
        )

        print(
            "py sql_to_json.py archivo.sql carpeta_destino"
        )

        sys.exit(1)

    sql_file = sys.argv[1]

    output_dir = (
        sys.argv[2]
        if len(sys.argv) > 2
        else DEFAULT_OUTPUT_DIR
    )

    sql_to_json(
        sql_file,
        output_dir
    )


if __name__ == "__main__":
    main()