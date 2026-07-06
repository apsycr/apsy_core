from urllib.parse import urlencode
import requests

from fastapi.responses import RedirectResponse

from modules.oauth.provider_base import ProviderBase


class GoogleProvider(ProviderBase):

	AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
	TOKEN_URL = "https://oauth2.googleapis.com/token"
	USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

	SCOPES = {
		"SEND": [
			"openid",
			"email",
			"profile",
			"https://www.googleapis.com/auth/gmail.send"
		],
		"READ": [
			"openid",
			"email",
			"profile",
			"https://www.googleapis.com/auth/gmail.readonly"
		],
		"BOTH": [
			"openid",
			"email",
			"profile",
			"https://www.googleapis.com/auth/gmail.modify"
		]
	}

	def __init__(self):

		super().__init__("google")

	# ==========================================
	# CONNECT
	# ==========================================

	def connect(
		self,
		uso="SEND",
		state=None
	):

		scopes = self.SCOPES.get(
			uso.upper(),
			self.SCOPES["SEND"]
		)

		params = {

			"client_id": self.client_id,

			"redirect_uri": self.redirect_uri,

			"response_type": "code",

			"scope": " ".join(scopes),

			"access_type": "offline",

			"prompt": "consent"

		}

		if state:
			params["state"] = state

		url = (
			self.AUTH_URL +
			"?" +
			urlencode(params)
		)

		return RedirectResponse(url)

	# ==========================================
	# CALLBACK
	# ==========================================

	def callback(
		self,
		code,
		state=None
	):

		response = requests.post(

			self.TOKEN_URL,

			data={

				"client_id": self.client_id,

				"client_secret": self.client_secret,

				"redirect_uri": self.redirect_uri,

				"grant_type": "authorization_code",

				"code": code

			}

		)

		token = response.json()

		access_token = token.get("access_token")

		refresh_token = token.get("refresh_token")

		expires_in = token.get("expires_in")

		user = requests.get(

			self.USERINFO_URL,

			headers={

				"Authorization":
					f"Bearer {access_token}"

			}

		).json()

		return {

			"ok": True,

			"provider": self.provider,

			"oauth_uid": user.get("id"),

			"correo": user.get("email"),

			"nombre": user.get("name"),

			"picture": user.get("picture"),

			"access_token": access_token,

			"refresh_token": refresh_token,

			"expires_in": expires_in,

			"scope": token.get("scope"),

			"state": state

		}

	# ==========================================
	# REFRESH TOKEN
	# ==========================================

	def refresh_token(
		self,
		refresh_token
	):

		response = requests.post(

			self.TOKEN_URL,

			data={

				"client_id": self.client_id,

				"client_secret": self.client_secret,

				"grant_type": "refresh_token",

				"refresh_token": refresh_token

			}

		)

		return response.json()

	# ==========================================
	# DISCONNECT
	# ==========================================

	def disconnect(self, **kwargs):

		return {
			"ok": True
		}