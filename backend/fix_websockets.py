import re

with open("tests/test_websockets.py", "r") as f:
    content = f.read()

content = content.replace('    with client.websocket_connect("/ws/collab") as ws:\n        try:\n            ws.receive()\n        except WebSocketDisconnect:\n            pass', '    import pytest\n    with pytest.raises(WebSocketDisconnect):\n        with client.websocket_connect("/ws/collab") as ws:\n            ws.receive()')

content = content.replace('    with client.websocket_connect("/ws/collab?token=invalid-jwt") as ws:\n        try:\n            ws.receive()\n        except WebSocketDisconnect:\n            pass', '    import pytest\n    with pytest.raises(WebSocketDisconnect):\n        with client.websocket_connect("/ws/collab?token=invalid-jwt") as ws:\n            ws.receive()')

with open("tests/test_websockets.py", "w") as f:
    f.write(content)
