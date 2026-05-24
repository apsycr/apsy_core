async def handle_auth(websocket, data):

    token = data.get("token")

    if not token:
        raise Exception("Auth sin token")

    # TODO:
    # validar token en DB

    await websocket.send_json({
        "success": 1,
        "type": "auth_ok"
    })