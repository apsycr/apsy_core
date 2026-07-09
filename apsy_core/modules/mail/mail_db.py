from datetime import datetime, timedelta
import random

from modules.db import ejecutar_api


class MailDB:

	def get_account(self,idtenant = 0):
		ejecutar_api(
			"""
			SELECT 
				provider,
				correo,
				access_token,
				refresh_token,
				client_id,
				client_secret
			FROM oauth_sucursales
			WHERE idtenant = %s
			AND uso = 'SEND'
			AND estado = 1
			LIMIT 1
			""",
			(idtenant,),
			"one")

	# ==========================================
	# GENERATE CODE
	# ==========================================

	def generate_code(
		self,
		tipo,
		correo,
		fingerprint=None,
		idtenant=None,
		minutos=10
	):

		codigo = str(
			random.randint(
				100000,
				999999
			)
		)

		fecha_expira = (
			datetime.now() +
			timedelta(minutes=minutos)
		)

		ejecutar_api(
			"""
			UPDATE mail_codes
			SET estado=0
			WHERE
				correo=%s
				AND tipo=%s
				AND estado=1
			""",
			(
				correo,
				tipo
			),
			"none"
		)

		ejecutar_api(
			"""
			INSERT INTO mail_codes(
				tipo,
				correo,
				codigo,
				fingerprint,
				idtenant,
				fecha_expira
			)
			VALUES(
				%s,
				%s,
				%s,
				%s,
				%s,
				%s
			)
			""",
			(
				tipo,
				correo,
				codigo,
				fingerprint,
				idtenant,
				fecha_expira
			),
			"none"
		)

		return codigo

	# ==========================================
	# VERIFY CODE
	# ==========================================

	def verify_code(
		self,
		correo,
		codigo
	):

		result = ejecutar_api(
			"""
			SELECT
				id,
				fecha_expira
			FROM mail_codes
			WHERE
				correo=%s
				AND codigo=%s
				AND estado=1
			ORDER BY id DESC
			LIMIT 1
			""",
			(
				correo,
				codigo
			),
			"one"
		)

		if not result:

			return False

		if result["fecha_expira"] < datetime.now():

			return False

		ejecutar_api(
			"""
			UPDATE mail_codes
			SET
				estado=2,
				fecha_validacion=NOW()
			WHERE id=%s
			""",
			(
				result["id"],
			),
			"none"
		)

		return True