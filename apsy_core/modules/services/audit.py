from modules.db import ejecutar_api

class Audit:

	@staticmethod
	def install(
		idinstall,
		evento,
		detalle="",
		fingerprint="",
		ip="",
		version=""
	):

		ejecutar_api(
			"""
			INSERT INTO auditar_installs
			(
				idinstall,
				evento,
				detalle,
				fingerprint,
				ip,
				version
			)
			VALUES
			(
				%s,
				%s,
				%s,
				%s,
				%s,
				%s
			)
			""",
			(
				idinstall,
				evento,
				detalle,
				fingerprint,
				ip,
				version
			),
			"none"
		)