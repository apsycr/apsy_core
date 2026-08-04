from modules.db import ejecutar_api


class db_release:

	@staticmethod
	def terminal_by_fingerprint(
		idtenant,
		fingerprint
	):

		result = ejecutar_api(
			"""
			SELECT
				id,
				idtenant,
				installation_token,
				fingerprint,
				id_dbversion,
				id_erpversion
			FROM crm_release_terminal
			WHERE
				idtenant = %s
				AND fingerprint = %s
			LIMIT 1
			""",
			(
				idtenant,
				fingerprint
			),
			"one"
		)

		if not result:
			return None

		return {
			"id": result['id'],
			"tenant": result['idtenant'],
			"installation_token": result['installation_token'],
			"fingerprint": result['fingerprint'],
			"id_dbversion": result['id_dbversion'],
			"id_erpversion": result['id_erpversion']
		}

	@staticmethod
	def terminal_create(
		idtenant,
		installation_token,
		fingerprint
	):

		ejecutar_api(
			"""
			INSERT INTO crm_release_terminal
			(
				idtenant,
				installation_token,
				fingerprint
			)
			VALUES
			(
				%s,
				%s,
				%s
			)
			""",
			(
				idtenant,
				installation_token,
				fingerprint
			),
			"none"
		)

		result = ejecutar_api(
			"""
			SELECT
				id,
				idtenant,
				installation_token,
				fingerprint,
				id_dbversion,
				id_erpversion
			FROM crm_release_terminal
			WHERE
				idtenant = %s
				AND fingerprint = %s
			LIMIT 1
			""",
			(
				idtenant,
				fingerprint
			),
			"one"
		)

		return {
			"id": result['id'],
			"tenant": result['idtenant'],
			"installation_token": result['installation_token'],
			"fingerprint": result['fingerprint'],
			"id_dbversion": result['id_dbversion'],
			"id_erpversion": result['id_erpversion']
		}

	@staticmethod
	def pending_releases(
		id_dbversion=None,
		id_erpversion=None
	):

		where = []

		params = []

		if id_dbversion:

			where.append(
				"(tipo = 'DB' AND id > %s)"
			)

			params.append(
				id_dbversion
			)

		else:

			where.append(
				"tipo = 'DB'"
			)

		if id_erpversion:

			where.append(
				"(tipo = 'ERP' AND id > %s)"
			)

			params.append(
				id_erpversion
			)

		else:

			where.append(
				"tipo = 'ERP'"
			)

		result = ejecutar_api(
			f"""
			SELECT
				id,
				tipo,
				version,
				descripcion,
				path
			FROM crm_release
			WHERE
				{' OR '.join(where)}
			ORDER BY
				tipo,
				id
			""",
			tuple(params),
			"all"
		)

		releases = []

		if not result:
			return releases

		for row in result:

			releases.append({
				"id": row.id,
				"tipo": row.tipo,
				"version": row.version,
				"descripcion": row.descripcion,
				"path": row.path
			})

		return releases

	@staticmethod
	def audit_create(
		idcrm_release_terminal,
		idrelease
	):

		ejecutar_api(
			"""
			INSERT INTO crm_audit_release
			(
				idcrm_release_terminal,
				idrelease,
				estado
			)
			VALUES
			(
				%s,
				%s,
				'PENDING'
			)
			""",
			(
				idcrm_release_terminal,
				idrelease
			),
			"none"
		)