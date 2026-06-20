from modules.db import ejecutar_api, ejecutar 
from modules.services.sync.apps import SYNC_APPS

def check_token(token):

	return ejecutar("""
		SELECT
			app,
			sucursal_id,
			terminal_id
		FROM ws_devices
		WHERE token = ?
		LIMIT 1
	""",
	(token,),
	"one")

def sync_init(app):

	if isinstance(app, dict):
		app = app.get("app")

	config = SYNC_APPS.get(app)

	if not config:
		return {
			"ok": False,
			"msg": f"App no soportada: {app}"
		}

	return {
		"ok": True,
		"version": config["version"],
		"tables": config["tables"]
	}

def compile_pull_manifest(device, body):

	app = device['app']

	payload = []

	for row in body["tables"]:

		manifest = get_manifest_table(
			app,
			row["tabla"]
		)

		if not manifest:
			continue

		pull = (
			manifest
			.get("server_side", {})
			.get("pull")
		)

		if not pull:
			continue

		payload.append({

			"tabla": row["tabla"],

			"rows": build_pull_sql(
				pull,
				row,
				device
			)

		})

	return {
		"ok": True,
		"payload": payload
	}

def get_manifest_table(app, tabla):

	for item in SYNC_APPS[app]["tables"]:

		if item["tabla"] == tabla:
			return item

	return None

def build_pull_sql(
	pull,
	row,
	device
):

	compiled = compile_fields(
	    pull["fields"]
	)

	table = pull["table"]

	pk = pull["pk"]

	ultimo_id = row.get(
		"ultimo_id",
		0
	)

	where = pull.get(
		"where",
		"1=1"
	)

	where = where.replace(
		"@@idsucursal",
		str(device["sucursal_id"])
	)

	sql = f"""
	SELECT
		 {",".join(compiled["selects"])}
	FROM {table} a

	{' '.join(compiled["joins"])}
	
	WHERE
		{pk} > {ultimo_id}
		AND {where}
	"""

	rows = ejecutar_api(
	    sql,
	    fetch="all"
	)

	return rows

def compile_fields(fields):

    selects = []
    joins = []

    alias = 1

    for field in fields:

        if isinstance(field, str):

            selects.append(
                f"a.{field}"
            )

        elif "expr" in field:

            selects.append(
                f"{field['expr']} AS {field['field']}"
            )

        elif "lookup" in field:

            join_alias = f"s{alias}"

            joins.append(f"""
            INNER JOIN sync_ids {join_alias}
                ON {join_alias}.id_servidor = a.{field['field']}
                AND {join_alias}.tabla = '{field['lookup']}'
            """)

            selects.append(
                f"{join_alias}.id_local AS {field['field']}"
            )

            alias += 1

    return {
        "selects": selects,
        "joins": joins
    }