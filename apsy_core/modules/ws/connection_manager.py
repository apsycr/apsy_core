class ConnectionManager:

    def __init__(self):

        self.connections = {}

    async def register(self, websocket, ws_server_id):

        self.connections[ws_server_id] = websocket

    def disconnect(self, websocket):

        dead = []

        for sid, ws in self.connections.items():

            if ws == websocket:
                dead.append(sid)

        for sid in dead:
            del self.connections[sid]

manager = ConnectionManager()