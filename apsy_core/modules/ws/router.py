from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from modules.services.mirror_manager import mirror_manager
from modules.services import push_watchdog

import logging

from modules.ws.manager import ws_connect
from modules.ws.local_manager import local_ws_manager

logger = logging.getLogger("ws-cloud")

router = APIRouter(prefix="/ws")

@router.websocket("/connect")
async def websocket_entry(websocket: WebSocket):

	await websocket.accept()

	try:
		while True:
			data = await websocket.receive_json()

			msg_type = data.get("type")

			if msg_type == "action_response":

				await mirror_manager.handle_message(
					data
				)

			elif msg_type in ("handshake", "auth"):

				await ws_connect(websocket, data)

			elif msg_type == "pull_pending_ok":

				push_watchdog.pull_pending_ok(
					websocket.device_id
				)


			elif msg_type == "pull_ok":

				push_watchdog.pull_ok(
					websocket.device_id
				)
			else:
				await websocket.send_json({
					"success": 0,
					"message": "Primer mensaje inválido"
				})

				await websocket.close(code=1008)
				return

	except WebSocketDisconnect:

		logger.warning("🔌 Cliente desconectado")

		device_id = getattr(
			websocket,
			"device_id",
			None
		)

		device_type = getattr(
			websocket,
			"device_type",
			None
		)

		if (
			device_type == "app"
			and device_id
		):

			push_watchdog.unregister_device(
				device_id
			)

	except Exception as e:

		logger.exception("❌ WS ERROR")

		try:
			await websocket.send_json({
				"success": 0,
				"message": str(e)
			})
		except:
			pass

		await websocket.close()

@router.get("/local/push/status")
async def debug_push_watchdog():

	return push_watchdog.status()

@router.get("/local/workflow")
async def debug_workflow():

	return {
		"cache": local_ws_manager.workflow_cache,
		"connections": {
			str(idtenant): {
				str(idusuario): len(sockets)
				for idusuario, sockets in users.items()
			}
			for idtenant, users in local_ws_manager.connections.items()
		}
	}

@router.websocket("/local/connect")
async def websocket_local(websocket: WebSocket):

	await websocket.accept()

	try:

		connected = await local_ws_manager.connect(
			websocket
		)

		if not connected:
			return 

		while True:
			data = await websocket.receive_json()
			
			await local_ws_manager.handle(
				websocket,
				data
			)

	except WebSocketDisconnect:

		await local_ws_manager.disconnect(
			websocket
		)

	except Exception:

		await local_ws_manager.disconnect(
			websocket
		)

		raise