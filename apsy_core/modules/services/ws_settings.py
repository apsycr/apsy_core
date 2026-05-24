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
        