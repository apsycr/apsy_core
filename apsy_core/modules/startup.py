from modules.services.cambio_dia.core import ejecutar_cambio_dia

def on_startup():
    ejecutar_cambio_dia()
