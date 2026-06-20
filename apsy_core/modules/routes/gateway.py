from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from modules.db import ejecutar

router = APIRouter(
	prefix="/gateway",
	tags=["gateway"]
)

@router.post("/device/status")
async def register_device(
	data: dict
):
	status = data.get("status")
	vid = data.get("id")

	ejecutar("""

		UPDATE ws_devices
		SET estado = %s
		WHERE id = %s

	""", (

		status,
		vid

	), "none")

	return {
		"ok": True
	}