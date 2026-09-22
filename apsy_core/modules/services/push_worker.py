from modules.db import get_connection

import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def push_worker():

	#logger.info("PUSH WORKER")

	conn = get_connection('db_api')

	try:
		cursor = conn.cursor(dictionary=True)

		cursor.execute("""
			SELECT
				id,
				uuid,
				idsucursal,
				idterminal,
				tabla,
				tabla_server,
				idregistro,
				accion,
				ins_columns,
				data,
				setter
			FROM sync_push_ids
			WHERE estado = 'PENDIENTE'
			ORDER BY id
			LIMIT 100
		""")

		rows = cursor.fetchall()

		for row in rows:

			try:

				data = json.loads(row["data"])

				if row["accion"] == "insertar":
					insertar(cursor, row, data)

				elif row["accion"] == "actualizar":
					actualizar(cursor, row, data)

				else:
					raise Exception(
						f"Accion desconocida: {row['accion']}"
					)

				cursor.execute("""
					UPDATE sync_push_ids
					SET estado = 'PROCESADO', processed_at = now()
					WHERE id = %s
				""", (row["id"],))

				conn.commit()

				logger.info(
					"PUSH OK %s uuid=%s tabla=%s id=%s",
					datetime.now().strftime("%H:%M:%S.%f")[:-3],
					row["uuid"],
					row["tabla"],
					row["idregistro"]
				)

			except Exception as e:

				conn.rollback()

				cursor.execute("""
					UPDATE sync_push_ids
					SET estado = 'ERROR',
						error = %s,
						processed_at = now()
					WHERE id = %s
				""", (str(e), row["id"]))

				conn.commit()

				# logger.exception(
				# 	"PUSH ERROR uuid=%s",
				# 	row["uuid"]
				# )

	finally:
		conn.close()

def insertar(cursor, row, data):

	columns = row["ins_columns"]

	placeholders = ",".join(["%s"] * len(data))

	sql = f"""
		INSERT INTO {row["tabla_server"]}
		({columns})
		VALUES ({placeholders})
	"""

	cursor.execute(sql, data)


def actualizar(cursor, row, data):

	setter = row["setter"].replace("?", "%s")

	sql = f"""
		UPDATE {row["tabla_server"]}
		SET {setter}
		WHERE id = %s
	"""

	params = list(data)
	params.append(row["idregistro"])

	cursor.execute(sql, params)