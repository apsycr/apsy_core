from fastapi import APIRouter, Request

from modules.services.db_install import db_install
from modules.services.db_release import db_release
from modules.services.audit import Audit

import json
import base64
from pathlib import Path


def build_release_package(
	tipo,
	version
):

	root = Path(
		f"/releases/{tipo}/{version}"
	)

	manifest_file = root / "manifest.json"

	if not root.exists():
		return []

	if not manifest_file.exists():
		raise Exception(
			f"Manifest not found: {manifest_file}"
		)

	with open(
		manifest_file,
		"r",
		encoding="utf-8"
	) as f:

		manifest = json.load(f)

	files = []

	for filename in manifest.get(
		"files",
		[]
	):

		file = root / filename

		if not file.exists():
			raise Exception(
				f"File not found: {filename}"
			)

		with open(
			file,
			"rb"
		) as content:

			files.append({
				"name": filename,
				"size": file.stat().st_size,
				"content": base64.b64encode(
					content.read()
				).decode("utf-8")
			})

	return files

router = APIRouter(
	prefix="/releases",
	tags=["releases"]
)


@router.post("/last_version")
async def last(request: Request):

	try:

		auth = request.headers.get(
			"Authorization",
			""
		)

		if not auth.startswith(
			"Bearer "
		):

			return {

				"ok": False,

				"msg": "Authorization requerido"

			}

		installation_token = auth.replace(
			"Bearer ",
			""
		).strip()

		fingerprint = request.headers.get("X-finger")

		if not installation_token:

			return {
				"success": False,
				"message": "Installation token required"
			}

		if not fingerprint:

			return {
				"success": False,
				"message": "Fingerprint required"
			}

		install = db_install.by_token(
			installation_token
		)

		if not install:

			return {
				"success": False,
				"message": "Invalid installation token"
			}

		terminal = db_release.terminal_by_fingerprint(
			install["tenant"],
			fingerprint
		)

		if not terminal:

			# terminal = db_release.terminal_create(
			# 	install["tenant"],
			# 	installation_token,
			# 	fingerprint
			# )

			return {
				"success": False,
				"message": "Invalid Terminal"
			}

		releases = db_release.pending_releases(
			terminal["id_dbversion"],
			terminal["id_erpversion"]
		)

		for release in releases:

			release["files"] = build_release_package(
				release["tipo"],
				release["version"]
			)

			db_release.audit_create(
				terminal["id"],
				release["id"]
			)

		return {
			"success": True,
			"release_terminal_id": terminal["id"],
			"releases": releases
		}

	except Exception as e:

		# Audit.error(
		# 	"releases.last_version",
		# 	str(e)
		# )

		return {
			"success": False,
			"message": str(e)
		}