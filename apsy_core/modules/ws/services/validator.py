def validar_identity(data: dict):
    required = ["hostname", "mac", "os", "app", "version", "payload"]

    for k in required:
        if k not in data:
            raise Exception(f"Falta campo {k}")

    if not isinstance(data["payload"], list):
        raise Exception("Payload de sucursales inválido")
