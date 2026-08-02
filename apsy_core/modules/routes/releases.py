from fastapi import APIRouter, Request

from modules.services.db_install import db_install
from modules.services.db_release import db_release
from modules.services.audit import Audit

from pathlib import Path
import base64


def build_release_package(
    tipo,
    version
):

    root = Path(
        f"/releases/{tipo}/{version}"
    )

    files = []

    if not root.exists():
        return files

    for file in root.iterdir():

        if not file.is_file():
            continue

        with open(
            file,
            "rb"
        ) as f:

            files.append({
                "name": file.name,
                "size": file.stat().st_size,
                "content": base64.b64encode(
                    f.read()
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

		data = await request.json()

		installation_token = data.get(
			"installation_token"
		)

		fingerprint = data.get(
			"fingerprint"
		)

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