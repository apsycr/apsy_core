from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from modules.mail.mail_sender import MailSender
from modules.mail.mail_db import MailDB

from datetime import datetime

router = APIRouter(
	prefix="/mail",
	tags=["mail"]
)

db = MailDB()

@router.post("/code")
async def code(request: Request):

	data = await request.json()

	action = data.get("action")

	if action == "send":

		codigo = db.generate_code(

			tipo=data.get("tipo", "INSTALL"),

			correo=data["correo"],

			fingerprint=data.get("fingerprint",""),

			idtenant=data.get("idtenant",0)
		)

		segundos_restantes = int(

		    (
		        codigo["fecha_expira"]
		        -
		        datetime.now()
		    ).total_seconds()

		)

		if codigo["nuevo"]:

			mail = MailSender()

			await mail.send(
				destino=data["correo"],
				asunto='Código de Solicitud de Instalación',
				titulo='Código APSY',
				mensaje=f'''
				<p>
					Utilice el siguiente código para continuar
					con la instalación del sistema.
				</p>

				<div style="
					text-align:center;
					margin:30px 0;
				">
					<span style="
						font-size:36px;
						font-weight:bold;
						color:#2563eb;
						letter-spacing:4px;
					">
						{codigo}
					</span>
				</div>

				<p>
					Este código expirará en 10 minutos.
				</p>
				'''
			)

		return JSONResponse({

		    "ok": True,
		    "nuevo": codigo['nuevo'],
		    "fecha_expira": segundos_restantes

		})

	elif action == "verify":

		ok = db.verify_code(

			correo=data["correo"],

			codigo=data["codigo"]
		)

		return JSONResponse({

			"ok": ok
		})

	return JSONResponse({

		"ok": False,

		"error": "Acción inválida"

	})