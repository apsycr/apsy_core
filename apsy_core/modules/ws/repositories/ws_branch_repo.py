from modules.db import get_db

def sync_sucursales(ws_server_id: int, sucursales: list):
    with get_db() as db:

        # obtener sucursales actuales
        db.execute("""
            SELECT idsucursal FROM ws_sucursales
            WHERE ws_server_id = ?
        """, (ws_server_id,))
        actuales = {r[0] for r in db.fetchall()}

        entrantes = {s["idsucursal"] for s in sucursales}

        # ──────────────────────────────
        # eliminar (desactivar)
        # ──────────────────────────────
        for ids in actuales - entrantes:
            db.execute("""
                UPDATE ws_sucursales
                SET activo = 0
                WHERE ws_server_id = ?
                AND idsucursal = ?
            """, (ws_server_id, ids))

        # ──────────────────────────────
        # insertar / actualizar
        # ──────────────────────────────
        for s in sucursales:
            #validar_cedula_unica(db, s["cedula"], ws_server_id)

            db.execute("""
                SELECT id FROM ws_sucursales
                WHERE ws_server_id = ?
                AND idsucursal = ?
            """, (ws_server_id, s["idsucursal"]))

            row = db.fetchone()

            if row:
                db.execute("""
                    UPDATE ws_sucursales SET
                        razon = ?,
                        access_token = ?,
                        activo = 1
                    WHERE id = ?
                """, (
                    s["razon"],
                    s["access_token"],
                    row[0]
                ))
            else:
                db.execute("""
                    INSERT INTO ws_sucursales
                    (ws_server_id, idsucursal, cedula, razon, access_token, activo)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (
                    ws_server_id,
                    s["idsucursal"],
                    s["cedula"],
                    s["razon"],
                    s["access_token"]
                ))

