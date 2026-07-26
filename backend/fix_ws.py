with open("tests/test_websockets.py", "r") as f:
    c = f.read()

import re
c = re.sub(
    r'with client\.websocket_connect\("/ws/collab"\) as ws:\n\s+pass',
    'from starlette.websockets import WebSocketDisconnect\n    import pytest\n    with pytest.raises(WebSocketDisconnect):\n        with client.websocket_connect("/ws/collab") as ws:\n            pass',
    c
)

c = re.sub(
    r'with client\.websocket_connect\("/ws/collab\?token=invalid-jwt"\) as ws:\n\s+pass',
    'with pytest.raises(WebSocketDisconnect):\n        with client.websocket_connect("/ws/collab?token=invalid-jwt") as ws:\n            pass',
    c
)

with open("tests/test_websockets.py", "w") as f:
    f.write(c)
