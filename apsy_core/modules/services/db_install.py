from modules.db import ejecutar_api

class db_install:

	@staticmethod
	def by_token(
		token
		):

		result = ejecutar_api(""" 

			SELECT
				id,
				idtenant,
				estado
			FROM crm_install
			WHERE token = %s
			LIMIT 1
			""",
			(
				token,
			),
			"one"
		)

		if result == None:
			return None

		return{
			"id"    : result.id,
			"tenant": result.idtenant,
			"estado": result.estado

		}

	@staticmethod
	def last_fingerprint(idinstall):

		result = ejecutar_api(
			"""
			SELECT
				fingerprint
			FROM
				auditar_installs
			WHERE
				idinstall = %s
			ORDER BY
				id DESC
			LIMIT 1
			""",
			(idinstall,),
			"one"
		)

		if not result:
			return None

		return result.fingerprint

	@staticmethod
	def by_fingerprint(
		tenant
	):
		resultado = ejecutar_api("""

			SELECT
				id,
				tipo,
				estado,
				device_uid as fingerprint
			FROM crm_terminales
			WHERE
				idtenant = %s
			LIMIT 1

			""",
			(	
				tenant,
			),
			"one")

		if not result:
			return None

		return {
			"fingerprint": fingerprint
		}
