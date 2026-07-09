from email.message import EmailMessage
from pathlib import Path

import mimetypes
import smtplib
import ssl
import aiohttp

class ZohoMail:


    def __init__(self, cuenta):

        self.cuenta = cuenta

        self.correo = cuenta["correo"]
        self.access_token = cuenta["access_token"]
        self.refresh_token = cuenta["refresh_token"]

    async def refresh_access_token(self):

        """
        Renueva token OAuth2 Zoho
        """

        url = "https://accounts.zoho.com/oauth/v2/token"


        data = {

            "refresh_token": self.refresh_token,

            "client_id": self.cuenta["client_id"],

            "client_secret": self.cuenta["client_secret"],

            "grant_type": "refresh_token"

        }


        async with aiohttp.ClientSession() as session:

            async with session.post(
                url,
                data=data
            ) as response:


                result = await response.json()


                if "access_token" not in result:

                    raise Exception(
                        f"Error renovando token Zoho: {result}"
                    )


                self.access_token = result["access_token"]


                return self.access_token



    async def send(
        self,
        destino:str,
        asunto:str,
        html:str,
        cc:list=None,
        cco:list=None,
        adjuntos:list=None
    ):

        if not self.access_token:

            await self.refresh_access_token()

        mensaje = EmailMessage()


        mensaje["From"] = self.correo

        mensaje["To"] = destino

        mensaje["Subject"] = asunto


        mensaje.set_content(
            "Este correo requiere un cliente HTML."
        )


        mensaje.add_alternative(
            html,
            subtype="html"
        )

        if adjuntos:

            for archivo in adjuntos:

                ruta = Path(archivo)

                if not ruta.exists():
                    continue

                mime_type, _ = mimetypes.guess_type(
                    str(ruta)
                )

                if mime_type:

                    maintype, subtype = mime_type.split(
                        '/',
                        1
                    )

                else:

                    maintype = "application"
                    subtype = "octet-stream"

                with open(ruta, "rb") as f:

                    mensaje.add_attachment(
                        f.read(),
                        maintype=maintype,
                        subtype=subtype,
                        filename=ruta.name
                    )

        oauth_string = (
            f"user={self.correo}\1"
            f"auth=Bearer {self.access_token}\1"
            "\1"
        )

        try:

            context = ssl.create_default_context()


            with smtplib.SMTP_SSL(
                "smtp.zoho.com",
                465,
                context=context
            ) as smtp:


                smtp.docmd(
                    "AUTH",
                    "XOAUTH2 " +
                    oauth_string.encode(
                        "utf-8"
                    ).hex()
                )


                smtp.send_message(
                    mensaje
                )


            return {

                "estado": True,

                "mensaje": "Correo enviado correctamente"

            }



        except Exception as e:

            # si falla por token expirado
            # intentamos renovar

            await self.refresh_access_token()


            raise Exception(
                f"Error enviando correo Zoho: {e}"
            )