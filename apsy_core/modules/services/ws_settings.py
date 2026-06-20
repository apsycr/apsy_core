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
            INSERT INTO ws_devices (
                device_id,
                nombre,
                hostname,
                ip,
                mac,
                app,
                version,
                token,
                sucursal_id,
                cedula,
                terminal_id,
                estado,
                created_at,
                updated_at,
                last_seen
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                1,
                NOW(),
                NOW(),
                NOW()
            )

            ON DUPLICATE KEY UPDATE

                nombre = VALUES(nombre),
                hostname = VALUES(hostname),
                ip = VALUES(ip),
                mac = VALUES(mac),
                app = VALUES(app),
                version = VALUES(version),
                sucursal_id = VALUES(sucursal_id),
                cedula = VALUES(cedula),
                terminal_id = VALUES(terminal_id),
                last_seen = NOW(),
                updated_at = NOW()
        """, [

            device["device_id"],
            device.get("nombre"),
            device.get("hostname"),
            device.get("ip"),
            device.get("mac"),
            device.get("app"),
            device.get("version"),
            device["token"],
            device.get("sucursal_id"),
            device.get("cedula"),
            device.get("terminal_id")
        ])

        return device

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
                "idsucursal": r['idsucursal'],
                "razon": r['razon'],
                "alias": r['alias']
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