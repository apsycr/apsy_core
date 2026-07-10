from modules.config import load_config
from datetime import datetime, timedelta
from pathlib import Path
from email.message import EmailMessage

import requests
import mimetypes
import smtplib
import ssl
import base64

class ZohoMail:


	def __init__(self, cuenta, db):

		self.cuenta = cuenta

		self.correo = cuenta["correo"]
		self.access_token = cuenta["access_token"]
		self.refresh_token = cuenta["refresh_token"]
		self.token_expira  = cuenta["token_expira"]
		self.account_id = cuenta['oauth_uid']
		self.load_config()
		self.db = db

	def load_config(self):

		cfg = load_config()

		providers = cfg.get("oauth", {}).get("providers", {})

		settings = providers['zoho']

		if not settings.get("enabled", False):
			raise Exception(
				f"Proveedor zoho deshabilitado."
			)

		self.client_id = settings["client_id"]
		self.client_secret = settings["client_secret"]

	async def refresh_access_token(self):

		"""
		Renueva token OAuth2 Zoho
		"""

		url = "https://accounts.zoho.com/oauth/v2/token"


		data = {

			"refresh_token": self.refresh_token,

			"client_id": self.client_id,

			"client_secret": self.client_secret,

			"grant_type": "refresh_token"

		}

		result = requests.post(
			url,
			data=data,
			timeout=15
		)

		result = result.json()

		if "access_token" not in result:

			raise Exception(
				f"Error renovando token Zoho: {result}"
			)


		self.access_token = result["access_token"]

		self.db.update_refresh(
			self.cuenta['id'],
			result["access_token"],
			result['expires_in'])

		return self.access_token

	async def ensure_valid_token(self):

	    if (
	        not self.access_token
	        or not self.token_expira
	        or datetime.now() >= (
	            self.token_expira -
	            timedelta(minutes=5)
	        )
	    ):

	        await self.refresh_access_token()


	async def send(
	    self,
	    destino:str,
	    asunto:str,
	    html:str,
	    cc:list=None,
	    cco:list=None,
	    adjuntos:list=None
	):

	    await self.ensure_valid_token()

	    headers = {

	        "Authorization":
	            f"Zoho-oauthtoken {self.access_token}"

	    }

	    payload = {

	        "fromAddress":
	            self.correo,

	        "toAddress":
	            destino,

	        "subject":
	            asunto,

	        "content":
	            html,

	        "mailFormat":
	            "html"

	    }

	    if cc:

	        payload["ccAddress"] = ",".join(cc)

	    if cco:

	        payload["bccAddress"] = ",".join(cco)

	    response = requests.post(

	        f"https://mail.zoho.com/api/accounts/{self.account_id}/messages",

	        headers=headers,

	        json=payload,

	        timeout=30

	    )

	    result = response.json()

	    if response.status_code not in (200, 201):

	        raise Exception(
	            f"Error enviando correo Zoho: {result}"
	        )

	    return result