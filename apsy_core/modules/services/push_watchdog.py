import asyncio
import logging


logger = logging.getLogger("push-watchdog")


# ============================================================
# CACHE
# ============================================================

devices_cache = {}


# ============================================================
# WATCHDOG
# ============================================================

_event = None
_task = None


# ============================================================
# INIT
# ============================================================

def init():

	global _event

	if _event is None:
		_event = asyncio.Event()


# ============================================================
# REGISTER DEVICE
# ============================================================

def register_device(
	device,
	websocket
):

	"""
	Registra un APP conectado.

	El websocket pertenece al device y vive
	mientras la conexión esté activa.
	"""

	init()

	device_id = device["id"]

	devices_cache[device_id] = {

		"id": device_id,

		"device_id": device.get(
			"device_id"
		),

		"idtenant": device.get(
			"idtenant",
			0
		),

		"idsucursal": device.get(
			"sucursal_id",
			device.get(
				"idsucursal",
				0
			)
		),

		"idterminal": device.get(
			"terminal_id",
			device.get(
				"idterminal",
				0
			)
		),

		"websocket": websocket,

		# ----------------------------------------
		# Pull
		# ----------------------------------------

		"pull_pending": True,

		"pull_sent": False,

	}


# ============================================================
# UNREGISTER
# ============================================================

def unregister_device(
	device_id
):

	if device_id not in devices_cache:
		return


	del devices_cache[
		device_id
	]

# ============================================================
# REQUEST PULL
# ============================================================

def request_pull(

	idtenant=0,
	idsucursal=0,
	idterminal=0

):

	init()

	encontrados = 0


	for device in devices_cache.values():

		# ========================================
		# GLOBAL
		# ========================================

		if (

			idtenant == 0
			and idsucursal == 0
			and idterminal == 0

		):

			device[
				"pull_pending"
			] = True

			device[
				"pull_sent"
			] = False

			encontrados += 1

			continue


		# ========================================
		# TENANT
		# ========================================

		if (

			device["idtenant"]
			!= idtenant

		):
			continue


		# ========================================
		# SUCURSAL
		# ========================================

		if (

			idsucursal != 0
			and
			device["idsucursal"]
			!= idsucursal

		):
			continue


		# ========================================
		# TERMINAL
		# ========================================

		if (

			idterminal != 0
			and
			device["idterminal"]
			!= idterminal

		):
			continue


		device[
			"pull_pending"
		] = True

		device[
			"pull_sent"
		] = False

		encontrados += 1

	_event.set()


# ============================================================
# ACK RECEPCION
# ============================================================

def pull_pending_ok(
	device_id
):

	device = devices_cache.get(
		device_id
	)

	if not device:
		return False


	device[
		"pull_sent"
	] = True


	return True


# ============================================================
# ACK FINAL
# ============================================================

def pull_ok(
	device_id
):

	device = devices_cache.get(
		device_id
	)

	if not device:
		return False


	device[
		"pull_pending"
	] = False

	device[
		"pull_sent"
	] = False

	return True


# ============================================================
# PENDING
# ============================================================

def get_pending():

	return [

		device

		for device
		in devices_cache.values()

		if device[
			"pull_pending"
		]

		and not device[
			"pull_sent"
		]

	]


# ============================================================
# WATCHDOG
# ============================================================

async def watchdog():

	while True:

		await _event.wait()

		_event.clear()


		try:

			pending = get_pending()


			for device in pending:

				device_id = device[
					"id"
				]

				websocket = device[
					"websocket"
				]


				try:

					await websocket.send_json({

						"type":
							"device_pull"

					})


					# --------------------------------
					# OJO
					# --------------------------------
					#
					# Aquí NO limpiamos pending.
					#
					# Tampoco consideramos que el
					# pull fue confirmado.
					#
					# Esperamos:
					#
					# pull_pending_ok
					#
					# --------------------------------

				except Exception as e:

					print(

						f"🐶 DEVICE PULL ERROR: "
						f"id={device_id} "
						f"{type(e).__name__}: "
						f"{str(e)}"

					)


		except Exception as e:

			logger.exception(
				"🐶 WATCHDOG ERROR"
			)


# ============================================================
# START
# ============================================================

def start():

	global _task

	init()


	if _task is not None:
		return


	loop = asyncio.get_running_loop()


	_task = loop.create_task(
		watchdog()
	)

def status():

	return {

		"devices": [

			{
				"id": device["id"],
				"device_id": device.get("device_id"),

				"idtenant":
					device.get("idtenant", 0),

				"idsucursal":
					device.get("idsucursal", 0),

				"idterminal":
					device.get("idterminal", 0),

				"pull_pending":
					device.get("pull_pending", False),

				"pull_sent":
					device.get("pull_sent", False),

				"connected":
					device.get("websocket") is not None

			}

			for device
			in devices_cache.values()

		],

		"total":
			len(devices_cache),

		"pending":
			len([
				d
				for d in devices_cache.values()
				if d.get("pull_pending")
			])

	}

def stop():

	global _task

	if _task is None:
		return

	_task.cancel()

	_task = None