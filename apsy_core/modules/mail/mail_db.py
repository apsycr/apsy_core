from datetime import datetime, timedelta
import random

from modules.db import ejecutar_api


class MailDB:

	def save_smtp(self,idtenant,
            host,
            puerto,
            seguridad,
            usuario,
            password,
            auth_type,
            remitente_nombre,
            uso):

		ejecutar_api(
		"""
        INSERT INTO smtp_sucursales (

            idtenant,
            host,
            puerto,
            seguridad,
            usuario,
            password,
            auth_type,
            remitente_nombre,
            uso,
            estado

        ) VALUES (

            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            1

        )
        """,
        (
            idtenant,
            host,
            puerto,
            seguridad,
            usuario,
            password,
            auth_type,
            remitente_nombre,
            uso
        ),
        'none'
        )

	def update_refresh(self,vid, access_token, token_expira):
		ejecutar_api("""
			UPDATE oauth_sucursales
			SET
				access_token=?,
				token_expira = DATE_ADD(
					NOW(),
					INTERVAL ? SECOND
				)
			WHERE id=?
			""",
			(access_token, token_expira, vid),
			'none')

	def get_account(self, idtenant=0):

	    cuenta = ejecutar_api(
	        """
	        SELECT
	            id,
	            provider,
	            correo,
	            access_token,
	            refresh_token,
	            token_expira,
	            oauth_uid
	        FROM oauth_sucursales
	        WHERE idtenant = %s
	        AND (uso = 'SEND' OR uso = 'BOTH')
	        AND estado = 1
	        LIMIT 1
	        """,
	        (idtenant,),
	        "one"
	    )

	    if cuenta:
	        return cuenta

	    return ejecutar_api(
	        """
	        SELECT
	            id,
	            'smtp' AS provider,
	            host,
	            puerto,
	            seguridad,
	            usuario,
	            password,
	            auth_type,
	            remitente_nombre
	        FROM smtp_sucursales
	        WHERE idtenant = %s
	        AND estado = 1
	        LIMIT 1
	        """,
	        (idtenant,),
	        "one"
	    )

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
		existe = ejecutar_api(
			"""
			SELECT
			    codigo,
			    fecha_expira
			FROM mail_codes
			WHERE
			    correo = ?
			    AND tipo= ?
			    AND estado = 1
			    AND fecha_expira > NOW()
			LIMIT 1
			""",
			(
				correo,
				tipo
			),
			'one')

		if not existe == None:
			 return {

			    "codigo": existe["codigo"],
			    "fecha_expira": existe["fecha_expira"],
			    "nuevo": False

			}

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

		return {

		    "codigo": codigo,
		    "fecha_expira": fecha_expira,
		    "nuevo": True

		}

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