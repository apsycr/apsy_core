from modules.db import ejecutar_api, ejecutar 
from modules.services.sync.apps import load_manifest
import logging
from datetime import datetime
logger = logging.getLogger("ws-server-local")

def check_token(token,tipo):

	return ejecutar("""
		SELECT
			app,
			sucursal_id,
			terminal_id
		FROM ws_devices
		WHERE token = ?
		and app = ?
		LIMIT 1
	""",
	(token,tipo,),
	"one")

def sync_init(app):

	if isinstance(app, dict):
		app = app.get("app")

	manifest = load_manifest(app)

	if not manifest:
		return {
			"ok": False,
			"error": f"App no soportada: {app}",
			"msg": "Manifest version mismatch"
		}

	return {
		"ok": True,
		"version": manifest["version"],
		"tables": manifest["tables"]
	}

def compile_pull_manifest(body,tipo):

	idsucursal 		= body['idsucursal']
	idterminal 		= body['idterminal']

	payload = []

	manifest = load_manifest(tipo)

	if not manifest:
		return {
			"ok": False,
			"msg": "Manifest not found"
		}

	version_manifest = manifest.get("version", 1)

	if body.get("manifest_version", 1) != version_manifest:

		return {
			"ok": False,
			"error": "manifest_version",
			"msj":"Manifest version mismatch",
			"manifest": manifest
		}

	tables_manifest = {
		table["tabla"]: table
		for table in manifest.get("tables", [])
	}

	for row in body["tables"]:

		tabla 		= row["tabla"]

		table_in 	= tables_manifest.get(tabla)

		if not table_in:
			continue

		table_version_server = table_in.get("client_side").get("version", 1)
		table_version_client = row.get("version", 1)

		if table_version_client != table_version_server:
			payload.append({
				"ok":False,
				"error": "table_version",
				"msg": "Table version mismatch",
				"manifest":table_in,
				"idmanifest": row["idmanifest"],
				"tabla": tabla,
			})
			continue

		pull = (
			table_in
			.get("server_side", {})
			.get("pull")
		)

		queue = (
			table_in
			.get("server_side", {})
			.get("queue")
		)

		if not pull:
			continue

		nombre_servidor = (
			table_in
			.get("server_side")
			.get("table_name", row["tabla"])
		)
		
		server_last_id = server_last(nombre_servidor)
		server_last_queue_id = server_last_queue(nombre_servidor)

		pull_sql = pull["sql"]

		pull_sql = pull_sql.replace(
			"@@last_id",
			str(server_last_id)
		)

		pull_args = extract_args_manifest(
			row,
			pull.get("args", {})
		)

		queue_sql = None
		queue_args = []

		if queue:

			queue_sql = queue["sql"]

			queue_args = extract_args_manifest(
				row,
				queue.get("args", {})
			)
		
		last_queue_id 	= row['ultimo_queue_id']

		payload.append({
				"ok": True,

				"tabla": row["tabla"],

				"insertar": build_pull_sql(
					pull_sql,
					pull_args,
				),

				"actualizar": build_queue_sql(
					row["tabla"],
					queue_sql,
					queue_args,
					idsucursal,
					idterminal,
					last_queue_id,
					server_last_queue_id
				) if queue_sql else [],

				"lookup": pull.get("lookup", {}),

				"update": pull.get("update", {}),

				"ultimo_id": server_last_id,
				"ultimo_queue_id": server_last_queue_id,
				"idmanifest": row["idmanifest"]

			})

	return {
		"ok": True,
		"payload": payload,
		"push_status" : get_push_status(idsucursal,idterminal)
	}

def get_push_status(idsucursal,idterminal):
	return ejecutar_api(
		"""
		SELECT 
			uuid,
			estado,
			error
		from
			sync_push_ids
		where  
			idsucursal = %s
			and idterminal = %s
			and processed_at is not null
		""",
		(
			idsucursal,
			idterminal,
		),
		"all"
	)

def server_last(tabla):
	result = ejecutar_api(
		f"""
		SELECT 
			COALESCE(MAX(id), 0) as ultima_linea
		from
			{tabla}
		""",
		(),
		"one"
	)

	return result['ultima_linea']

def server_last_queue(tabla):
	result = ejecutar_api(
		"""
		SELECT 
			COALESCE(MAX(id), 0) AS ultima_linea
		from
			sync_queue
		where
			tabla = %s
		""",
		(
			tabla,
		),
		"one"
	)

	return result['ultima_linea']

def build_queue_sql(
	tabla,
	tabla_sql,
	tabla_args,
	idsucursal,
	idterminal,
	last_queue_id,
	server_last_queue_id
):

	sql = f"""
		SELECT
			b.*
		FROM
			sync_queue a
		JOIN
			(
				{tabla_sql}
			) b
				ON b.id = a.idregistro
		WHERE
			a.id > %s
			AND a.tabla = %s
			AND a.idsucursal = %s
			AND a.idterminal = %s
			AND a.id <= %s
		GROUP BY
			a.idregistro
	"""

	# argumentos de sync_queue
	tabla_args.extend([
		last_queue_id,
		tabla,
		idsucursal,
		idterminal,
		server_last_queue_id
	])

	return ejecutar_api(
		sql,
		tuple(tabla_args),
		"all",
		dictionary=False
	)

def extract_args_manifest(row, pull_args):
	
	args = []

	for param in pull_args:

		if param not in row:
			raise ValueError(
				f"Parametro '{param}' no existe"
			)

		args.append(row[param])

	return args

def build_pull_sql(sql,args):

	return ejecutar_api(
		sql,
		tuple(args),
		fetch="all"
	)

###### PUSH ######

def compile_push(body, tipo):

	idsucursal = body["idsucursal"]
	idterminal = body["idterminal"]
	rows = body.get("info", [])

	ack_push = body.get("ack_push",[])
	ack_push = body.get("ack_push", [])

	if ack_push:
		vaciar_estados(
			idsucursal,
			idterminal,
			ack_push
		)

	if not rows:
		return {
			"ok": True,
			"insertados": 0
		}

	valores = []

	for row in rows:

		valores.append((
			row["uuid"],
			idsucursal,
			idterminal,
			row["tabla"],
			row["idregistro"],
			row["accion"],
			row['tabla_server'],
			row["ins_columns"],
			row["data"],
			row["setter"],
			"PENDIENTE"
		))

	placeholders = ",".join(
		["(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"] * len(valores)
	)

	params = []

	for valor in valores:
		params.extend(valor)

	sql = f"""
		INSERT INTO sync_push_ids
		(
			uuid,
			idsucursal,
			idterminal,
			tabla,
			idregistro,
			accion,
			tabla_server,
			ins_columns,
			data,
			setter,
			estado
		)
		VALUES {placeholders}
		ON DUPLICATE KEY UPDATE
			uuid = uuid
	"""

	result = ejecutar_api(
		sql,
		tuple(params),
		"none"
	)
	
	return {
		"ok": True,
		"insertados": len(rows)
	}

def vaciar_estados(idsucursal, idterminal, ack):

	placeholders = ",".join("?" for _ in ack)
	logger.info(
		"UUID DELETE %s",
		datetime.now().strftime("%H:%M:%S.%f")[:-3],
		ack
	)
	ejecutar_api(
		f"""
		DELETE FROM sync_push_ids
		WHERE
			idsucursal = ?
			AND idterminal = ?
			AND uuid IN ({placeholders})
		""",
		(
			idsucursal,
			idterminal,
			*ack
		),
		"none"
	)

def sync_queue(body):
	codigo = body["codigo"]
	idregistro = body["idregistro"]

	return {
		"ok": True,
		"prueba": codigo*idregistro
	}