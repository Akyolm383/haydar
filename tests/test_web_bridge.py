import time
import pytest
from core.web_bridge import WebBridgeServer


def test_web_bridge_server_lifecycle():
    bridge = WebBridgeServer(host="127.0.0.1", port=8777)
    assert bridge.is_running is False
    assert bridge.is_connected() is False

    # Start server
    bridge.start()
    time.sleep(0.3)
    assert bridge.is_running is True

    # When no clients connected, send_command returns no_extension status
    res = bridge.send_command(action="click_button", target="sonraki bölüm")
    assert res["status"] == "no_extension"
    assert "bağlı değil" in res["message"]

    # Clean stop
    bridge.stop()
    time.sleep(0.2)
