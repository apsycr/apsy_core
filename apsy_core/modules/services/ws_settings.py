from modules.db import get_db

def get_setting(key):
    with get_db() as db:
        db.execute(
            "SELECT setting_value FROM ws_settings WHERE setting_key = %s",
            (key,)
        )
        row = db.fetchone()
        return row['setting_value'] if row else ""

def set_setting(key: str, value: str):
    with get_db() as db:
        db.execute("""
            INSERT INTO ws_settings (setting_key, setting_value)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
        """, (key, value))

def guardar_en_ws_devices(device):
    with get_db() as db:
        db.execute("""
            INSERT OR REPLACE INTO ws_devices
            (device_id, nombre, mac, token, tipo, sucursal_id, terminal_id, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, [
            device["device_id"],
            device["nombre"],
            device["mac"],
            device["token"],
            device["tipo"],
            device["sucursal_id"],
            device["terminal_id"]
        ])

def get_mirrors(ws_server_id):

    with get_db() as db:

        db.execute("""

            SELECT
                idsucursal,
                razon,
                alias

            FROM ws_sucursales

            WHERE ws_server_id = ?
            AND activo = 1

        """, (ws_server_id,))

        rows = db.fetchall()

        return [

            {
                "idsucursal": r[0],
                "razon": r[1],
                "alias": r[2]
            }

            for r in rows

        ]

def sync_ws_mirrors(mirrors):

    with get_db() as db:

        actuales = set()

        db.execute("""
            SELECT idsucursal
            FROM ws_mirrors
        """)

        for r in db.fetchall():
            actuales.add(r[0])

        entrantes = {
            m["idsucursal"]
            for m in mirrors
        }

        # ======================================
        # DESACTIVAR
        # ======================================

        for ids in actuales - entrantes:

            db.execute("""

                UPDATE ws_mirrors
                SET activo = 0
                WHERE idsucursal = ?

            """, (ids,))

        # ======================================
        # UPSERT
        # ======================================

        for m in mirrors:

            db.execute("""

                SELECT idsucursal
                FROM ws_mirrors
                WHERE idsucursal = ?

            """, (m["idsucursal"],))

            row = db.fetchone()

            if row:

                db.execute("""

                    UPDATE ws_mirrors SET

                        razon = ?,
                        alias = ?,
                        activo = 1,
                        updated_at = CURRENT_TIMESTAMP

                    WHERE idsucursal = ?

                """, (

                    m["razon"],
                    m["alias"],
                    m["idsucursal"]

                ))

            else:

                db.execute("""

                    INSERT INTO ws_mirrors
                    (
                        idsucursal,
                        razon,
                        alias,
                        activo
                    )
                    VALUES (?, ?, ?, 1)

                """, (

                    m["idsucursal"],
                    m["razon"],
                    m["alias"]

                ))