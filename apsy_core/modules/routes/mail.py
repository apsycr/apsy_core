from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from modules.mail.mail_db import MailDB

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

        return JSONResponse({

            "ok": True,

            "codigo": codigo  # temporal para pruebas
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