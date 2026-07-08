from modules.oauth.factory import OAuthFactory
from modules.oauth.oauth_db import OAuthDB
from modules.oauth.oauth_html import OAuthHTML
from modules.oauth.oauth_state import OAuthState


class OAuth:

	def __init__(self):

		self.db = OAuthDB()
		self.html = OAuthHTML()

	# ==========================================
	# CONNECT
	# ==========================================

	def connect(
		self,
		provider,
		context=None
	):
		context = context or {}

		state = OAuthState.encode(context or {})

		return OAuthFactory.create(provider).connect(
			state=state
		)

	# ==========================================
	# CALLBACK
	# ==========================================

	def callback(
		self,
		provider,
		code,
		state=None
	):

		result = OAuthFactory.create(provider).callback(
			code=code,
			state=state
		)

		if not result["ok"]:

			return self.html.error(
				result.get("error","No fue posible conectar la cuenta.")
			)

		context  = OAuthState.decode(state)

		self.db.save(

			idtenant=context["idtenant"],

			provider=result["provider"],

			oauth_uid=result["oauth_uid"],

			correo=result["correo"],

			access_token=result["access_token"],

			refresh_token=result["refresh_token"],

			expires_in=result["expires_in"],

			scope=result["scope"],

			uso=context["uso"],

			dc=context["dc"],

		)

		return self.html.ok(
			correo=result["correo"],
			oauth_uid=result["oauth_uid"]
		)

	# ==========================================
	# REFRESH TOKEN
	# ==========================================

	def refresh_token(
		self,
		provider,
		refresh_token
	):

		return OAuthFactory.create(provider).refresh_token(
			refresh_token
		)

	# ==========================================
	# DISCONNECT
	# ==========================================

	def disconnect(
		self,
		provider,
		idsucursal
	):

		self.db.disconnect(
			idsucursal,
			provider
		)

		return {
			"ok":True
		}