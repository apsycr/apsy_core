import logging
from collections import defaultdict
from fastapi import WebSocket

from modules.db import ejecutar_api

logger = logging.getLogger("ws-local")


class LocalWSManager:

	workflow_cache = {}

	def __init__(self):

		# {
		#     idtenant: {
		#         idusuario: {
		#             websocket,
		#             websocket,
		#         }
		#     }
		# }
		self.connections = defaultdict(
			lambda: defaultdict(set)
		)

		# {
		#     websocket: {
		#         idtenant,
		#         idusuario,
		#     }
		# }
		self.clients = {}


	# =========================================================
	# CONEXIÓN
	# =========================================================

	async def connect(
		self,
		websocket: WebSocket
	):

		session = await self.authenticate(
			websocket
		)

		if not session:

			await websocket.close(
				code=1008
			)

			return False


		idtenant = session["idtenant"]
		idusuario = session["idusuario"]


		self.connections[
			idtenant
		][
			idusuario
		].add(
			websocket
		)


		self.clients[
			websocket
		] = {
			"idtenant": idtenant,
			"idusuario": idusuario
		}


		logger.info(
			"🟢 WS LOCAL conectado "
			"tenant=%s usuario=%s conexiones=%s",
			idtenant,
			idusuario,
			len(
				self.connections[
					idtenant
				][
					idusuario
				]
			)
		)


		await websocket.send_json({

			"success": 1,

			"type": "auth",

			"data": {
				"idtenant": idtenant,
				"idusuario": idusuario
			}

		})


		return True


	# =========================================================
	# AUTENTICACIÓN
	# =========================================================

	async def authenticate(
		self,
		websocket: WebSocket
	):

		cookies = websocket.cookies


		# -----------------------------------------------------
		# Token de sesión
		# -----------------------------------------------------

		token = cookies.get("apsy_token")


		if not token:

			logger.warning(
				"🔒 WS LOCAL sin token"
			)

			return None


		session = await self.validate_token(
			token
		)


		if not session:

			logger.warning(
				"🔒 WS LOCAL token inválido"
			)

			return None


		return session


	# =========================================================
	# VALIDACIÓN DEL TOKEN
	# =========================================================

	async def validate_token(
		self,
		token
	):

		session_data = ejecutar_api('''
				SELECT user_id from auth_tokens where token = %s
			''',
				(token,),
				"one"
			)

		return {
			"idtenant":1,
			"idusuario": session_data['user_id'] 
		}


	# =========================================================
	# MENSAJES RECIBIDOS
	# =========================================================

	async def handle(
		self,
		websocket: WebSocket,
		data: dict
	):

		msg_type = data.get(
			"type"
		)

		# -----------------------------------------------------
		# Cambios en Solicitud
		# -----------------------------------------------------

		if msg_type == "refresh_solicitud":

		    await self.refresh_solicitud(
		        data["solicitud"]
		    )

		    return

		# -----------------------------------------------------
		# Inicializar Workflow
		# -----------------------------------------------------

		if msg_type == "workflow_init":

			await self.workflow_init(
				websocket
			)

			return


		# -----------------------------------------------------
		# Ping
		# -----------------------------------------------------

		if msg_type == "ping":

			await websocket.send_json({

				"success": 1,

				"type": "pong"

			})

			return


		logger.warning(
			"⚠️ WS LOCAL mensaje desconocido: %s",
			msg_type
		)


	# =========================================================
	# WORKFLOW INICIAL
	# =========================================================

	async def workflow_init(
		self,
		websocket: WebSocket
	):

		client = self.clients.get(
			websocket
		)

		if not client:

			return


		idtenant = client[
			"idtenant"
		]

		idusuario = client[
			"idusuario"
		]

		if idusuario not in self.workflow_cache:

			self.workflow_cache[idusuario] = {
				"solicitudes": 0,
				"responsabilidades": 0,
				"alertas": 0,
				"personal": 0,
				"total": 0,
				"cached": 0
			}

			await self.refresh_workflow(
				idusuario
			)
		else:
			self.workflow_cache[idusuario]['cached'] = 1

		#await self.emit_workflow(
		#	idusuario
		#)

		data = self.workflow_cache[idusuario]


		await websocket.send_json({

			"success": 1,

			"type": "workflow",

			"data": data

		})


	# =========================================================
	# EMITIR A UN USUARIO
	# =========================================================

	async def emit_user(
		self,
		idtenant,
		idusuario,
		data: dict
	):

		sockets = self.connections.get(
			idtenant,
			{}
		).get(
			idusuario,
			set()
		)


		if not sockets:

			return


		disconnected = []


		for websocket in sockets:

			try:

				await websocket.send_json(
					data
				)

			except Exception:

				disconnected.append(
					websocket
				)


		for websocket in disconnected:

			await self.disconnect(
				websocket
			)

	#
	# ACTUALIZAR DESDE LA BASE A MEMORIA EL CLIENTE EN EL CACHE DEL WORKFLOW
	#

	async def refresh_workflow(
		self,
		idusuario
	):

		if idusuario not in self.workflow_cache:
			return

		data = ejecutar_api("""
				CALL sp_getSolicitudes(%s,0,4,0)
			""",
			(idusuario,),
			"one")

		self.workflow_cache[idusuario]['solicitudes'] = data['solicitudes']


	# =========================================================
	# EMITIR A TODO UN TENANT
	# =========================================================

	async def emit_tenant(
		self,
		idtenant,
		data: dict
	):

		users = self.connections.get(
			idtenant,
			{}
		)


		for idusuario in list(
			users.keys()
		):

			await self.emit_user(
				idtenant,
				idusuario,
				data
			)


	# =========================================================
	# WORKFLOW DE UN USUARIO
	# =========================================================

	async def emit_workflow(
		self,
		idtenant,
		idusuario,
		data
	):

		await self.emit_user(

			idtenant,

			idusuario,

			{

				"success": 1,

				"type": "workflow",

				"data": data

			}

		)


	# =========================================================
	# WORKFLOW DE TODO EL TENANT
	# =========================================================

	async def emit_workflow_tenant(
		self,
		idtenant,
		data
	):

		await self.emit_tenant(

			idtenant,

			{

				"success": 1,

				"type": "workflow",

				"data": data

			}

		)

	async def refresh_solicitud(
	    self,
	    idsolicitud
	):

	    result = ejecutar_api(
	        "call sp_getSolicitudes(%s,0,5,0)",
	        (idsolicitud,),
	        "all"
	    )

	    for row in result:

	        self.workflow_cache[row['usuario']]['solicitudes'] = row['solicitudes']

	# =========================================================
	# DESCONECTAR
	# =========================================================

	async def disconnect(
		self,
		websocket: WebSocket
	):

		client = self.clients.pop(
			websocket,
			None
		)


		if not client:

			return


		idtenant = client[
			"idtenant"
		]

		idusuario = client[
			"idusuario"
		]


		users = self.connections.get(
			idtenant
		)


		if users:

			sockets = users.get(
				idusuario
			)


			if sockets:

				sockets.discard(
					websocket
				)


				if not sockets:

					users.pop(
						idusuario,
						None
					)


			if not users:

				self.connections.pop(
					idtenant,
					None
				)


		logger.info(
			"🔴 WS LOCAL desconectado "
			"tenant=%s usuario=%s",
			idtenant,
			idusuario
		)


# =============================================================
# INSTANCIA GLOBAL
# =============================================================

local_ws_manager = LocalWSManager()