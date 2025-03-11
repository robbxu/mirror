import socketio


manager = socketio.AsyncRedisManager('redis://redis:6379')
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    client_manager=manager
)
asgi = socketio.ASGIApp(sio, socketio_path="/ws/socket.io") # https://github.com/fastapi/fastapi/discussions/10970


# https://github.com/miguelgrinberg/python-socketio/issues/650
@sio.on("connect")
async def connect(sid, environ, auth) -> None:
    # https://stackoverflow.com/questions/69221200/socket-io-joining-multiple-rooms-on-connection
    await sio.emit('login', sid, room=sid)
    print(f"Socket connected: {sid}")

@sio.on("disconnect")
async def disconnect(sid) -> None:
    print(f"Socket disconnected: {sid}")
# https://pythonspeed.com/articles/docker-connection-refused/

@sio.on('join')
async def join_room(sid, data):
    room = data["room"]
    await sio.enter_room(sid, room)
    print(f"Sid {sid} joined room: {room}")


@sio.on('message')
async def print_message(sid, message):
    print("Socket ID: ", sid)
    print(message)

