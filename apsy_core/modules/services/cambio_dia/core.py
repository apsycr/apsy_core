from datetime import date
from modules.db import get_control, set_control
from modules.services.cambio_dia.rrhh import procesar_rrhh
from modules.services.backup import validar_backup

def ejecutar_cambio_dia():
    hoy = date.today().isoformat()
    ultima = get_control("ultima_fecha_cambio_dia")

    if ultima == hoy:
        return

    print("[CAMBIO_DIA] Ejecutando procesos diarios")

    procesar_rrhh()
    validar_backup()
    #actualizar_tipo_cambio()

    set_control("ultima_fecha_cambio_dia", hoy)

# MEJORAS
# ultima_fecha_cambio_dia

# Puedes llevar control individual:

# control
# -------------------------
# tipo_cambio_2026-05-07
# backup_2026-05-07
# rrhh_2026-05-07

# o:

# control_jobs
# -------------------------
# job
# ultima_ejecucion