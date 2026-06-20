from modules.db import get_db
import secrets
import datetime

def upsert_device(identity: dict):
    now = datetime.datetime.now()

    with get_db() as db:
        db.execute("""
            SELECT id, mac FROM ws_servers
            WHERE hostname = ?
        """, (identity["hostname"],))

        row = db.fetchone()

        # ──────────────────────────────
        # Servidor ya existe
        # ──────────────────────────────
        if row:
            ws_id, mac_db = row

            if mac_db != identity["mac"]:
                raise Exception(
                    "Cambio de servidor detectado. Reautorización requerida."
                )

            token = secrets.token_hex(32)

            db.execute("""
                UPDATE ws_servers SET
                    os = ?, version = ?, app = ?,
                    token = ?, last_seen = ?
                WHERE id = ?
            """, (
                identity["os"],
                identity["version"],
                identity["app"],
                token,
                now,
                ws_id
            ))

            return {"id": ws_id, "token": token}

        # ──────────────────────────────
        # Servidor nuevo
        # ──────────────────────────────
        token = secrets.token_hex(32)

        db.execute("""
            INSERT INTO ws_servers
            (hostname, mac, os, version, app, token, activo, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            identity["hostname"],
            identity["mac"],
            identity["os"],
            identity["tipo"],
            identity["app"],
            token,
            now
        ))

        return {"id": db.lastrowid, "token": token}
