from fastapi import APIRouter, Request
from modules.services.install import db_install
from modules.services.audit import Audit

router = APIRouter(
	prefix="/install",
	tags=["install"]
)

@router.post("/status")
async def status(request: Request):

	token = request.headers.get(
		"Authorization",
		""
	)

	fingerprint = request.headers.get(
		"X-finger",
		""
	)

	if token.startswith("Bearer "):
		token = token[7:]

	if not token:
		return {
			"status": "SIN_INSTALAR"
		}

	instalacion = db_install.by_token(token)

	if not instalacion:

		Audit.install(
			0,
			"TOKEN_NOT_FOUND",
			f"Token: {token}",
			fingerprint=fingerprint,
			ip=request.client.host
		)

		return {
			"status": "SIN_INSTALAR"
		}

	if not fingerprint:

		Audit.install(
			instalacion["id"],
			"FINGERPRINT_EMPTY",
			"Fingerprint vacío",
			ip=request.client.host
		)

	terminal = db_terminal.by_fingerprint(
	    instalacion["tenant"],
	    fingerprint
	)

	if not terminal:

	    Audit.install(
	        instalacion["id"],
	        "FINGERPRINT_DESCONOCIDO",
	        f"Fingerprint: {fingerprint}"
	    )

	    return {
	        "status": "SIN_INSTALAR"
	    }

	if (
		terminal["fingerprint"]
		and
		terminal["fingerprint"] != fingerprint
	):

		Audit.install(
			instalacion["id"],
			"FINGERPRINT_CHANGED",
			f"Original: {terminal['fingerprint']} | Actual: {fingerprint}",
			fingerprint=fingerprint,
			ip=request.client.host
		)

	return {
		"status": instalacion["estado"]
	}