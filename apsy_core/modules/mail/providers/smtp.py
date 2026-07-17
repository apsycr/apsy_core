import os
import smtplib

from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders


class SMTPMail:

    def __init__(self, cuenta):

        self.cuenta = cuenta

        self.host = cuenta["host"]
        self.port = int(cuenta["puerto"])
        self.security = cuenta["seguridad"]
        self.username = cuenta["usuario"]
        self.password = cuenta["password"]
        self.auth_type = cuenta["auth_type"]

        self.from_name = (
            cuenta.get("remitente_nombre")
            or "APSY"
        )


    async def send(
        self,
        destino: str,
        asunto: str,
        html: str,
        cc: list = None,
        cco: list = None,
        adjuntos: list = None,
        fromName: str = None
    ):

        cc = cc or []
        cco = cco or []
        adjuntos = adjuntos or []

        remitente = fromName or self.from_name

        msg = MIMEMultipart()

        msg["Subject"] = asunto
        msg["From"] = f"{remitente} <{self.username}>"
        msg["To"] = destino

        if cc:
            msg["Cc"] = ",".join(cc)

        msg.attach(
            MIMEText(
                html,
                "html",
                "utf-8"
            )
        )

        for archivo in adjuntos:

            if not os.path.exists(archivo):
                continue

            with open(archivo, "rb") as f:

                part = MIMEBase(
                    "application",
                    "octet-stream"
                )

                part.set_payload(
                    f.read()
                )

            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(archivo)}"'
            )

            msg.attach(part)

        destinatarios = [destino]

        destinatarios.extend(cc)
        destinatarios.extend(cco)

        if self.security == "SSL":

            server = smtplib.SMTP_SSL(
                self.host,
                self.port,
                timeout=30
            )

        else:

            server = smtplib.SMTP(
                self.host,
                self.port,
                timeout=30
            )

            if self.security == "TLS":

                server.starttls()

        try:

            if self.auth_type == "PASSWORD":

                server.login(
                    self.username,
                    self.password
                )

            elif self.auth_type == "OAUTH2":

                raise Exception(
                    "SMTP OAuth2 aún no implementado"
                )

            else:

                raise Exception(
                    f"Tipo de autenticación no soportado: {self.auth_type}"
                )

            server.sendmail(
                self.username,
                destinatarios,
                msg.as_string()
            )

        finally:

            server.quit()

        return {
            "status": {
                "code": 200,
                "description": "success"
            }
        }