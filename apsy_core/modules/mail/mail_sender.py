from modules.mail.mail_template import render_template
from modules.mail.mail_db import MailDB

from datetime import datetime

class MailSender:

    def __init__(self):

        self.db = MailDB()

    async def send(
        self,
        destino,
        asunto,
        titulo,
        mensaje,
        boton_texto=None,
        boton_url=None,
        adjuntos:list = None,
        cc:list = None,
        cco:list = None,
        idtenant=0
    ):

        cuenta = self.db.get_account(idtenant)

        if not cuenta:

            raise Exception(
                "No existe una cuenta configurada para envío de correo"
            )


        html = render_template(
            titulo,
            mensaje,
            boton_texto,
            boton_url
        )

        provider = cuenta["provider"]

        if provider=="google":
            print(123)
            #from modules.mail.providers.google import GoogleMail

            #mail = GoogleMail(cuenta)

        elif provider=="zoho":

            from modules.mail.providers.zoho import ZohoMail

            mail = ZohoMail(cuenta,self.db)

        elif provider=="microsoft":
            print(123)
            #from modules.mail.providers.microsoft import MicrosoftMail

            #mail = MicrosoftMail(cuenta)

        else:

            raise Exception(
                f"Proveedor no soportado {provider}"
            )

        return await mail.send(
            destino=destino,
            asunto=asunto,
            html=html,
            adjuntos=adjuntos
        )