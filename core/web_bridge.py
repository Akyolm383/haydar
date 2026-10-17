import asyncio
import json
import logging
import threading
import uuid
from typing import Any, Dict, Optional, Set

try:
    from websockets.asyncio.server import Server, serve
except ImportError:
    # Older websockets fallback
    from websockets.server import WebSocketServer as Server, serve

logger = logging.getLogger("HaydarWebBridge")


class WebBridgeServer:
    """
    Local WebSocket Bridge Server for Haydar Browser Extension.
    Allows Haydar to send DOM automation commands (click buttons, scroll, skip intro/ads)
    directly to the active browser tab via a Chromium extension.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.connected_clients: Set[Any] = set()
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.server: Optional[Any] = None
        self.stop_event: Optional[asyncio.Event] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False

    def start(self) -> None:
        """Starts the WebSocket bridge server in a background daemon thread."""
        if self.is_running:
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, name="HaydarWebBridgeThread", daemon=True)
        self.thread.start()

    def _run_loop(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._serve())
        except Exception as e:
            logger.error(f"WebBridge server error: {e}")
        finally:
            self.is_running = False
            try:
                self.loop.close()
            except Exception:
                pass

    async def _serve(self) -> None:
        self.stop_event = asyncio.Event()
        async with serve(self._handle_client, self.host, self.port) as server:
            self.server = server
            logger.info(f"Haydar Web Bridge running at ws://{self.host}:{self.port}")
            await self.stop_event.wait()

    async def _handle_client(self, websocket: Any) -> None:
        """Handles lifecycle and messages from connected browser extensions."""
        self.connected_clients.add(websocket)
        logger.info(f"Browser extension connected from {websocket.remote_address}")
        try:
            async for raw_msg in websocket:
                try:
                    data = json.loads(raw_msg)
                    msg_id = data.get("id")
                    if msg_id and msg_id in self.pending_responses:
                        future = self.pending_responses.pop(msg_id)
                        if not future.done():
                            future.set_result(data)
                except Exception as ex:
                    logger.warning(f"Failed to parse message from extension: {ex}")
        except Exception as e:
            logger.debug(f"Extension client disconnected: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info("Browser extension disconnected")

    def is_connected(self) -> bool:
        """Returns True if at least one browser extension is currently connected."""
        return len(self.connected_clients) > 0

    def send_command(
        self,
        action: str,
        target: str = "",
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 2.5,
    ) -> Dict[str, Any]:
        """
        Sends an automation command to the browser extension and waits for execution response.
        Thread-safe method callable from any Haydar thread.
        """
        if not self.is_running or not self.loop:
            return {"status": "server_stopped", "message": "Web bridge sunucusu çalışmıyor"}

        if not self.is_connected():
            return {
                "status": "no_extension",
                "message": "Tarayıcı eklentisi bağlı değil",
            }

        msg_id = str(uuid.uuid4())
        payload = {
            "id": msg_id,
            "action": action,
            "target": target,
            "params": params or {},
        }

        coro = self._dispatch_and_wait(msg_id, payload, timeout)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)

        try:
            return future.result(timeout=timeout + 0.5)
        except Exception as e:
            logger.warning(f"send_command timeout or error: {e}")
            return {"status": "timeout", "message": "Zaman aşımı"}

    async def _dispatch_and_wait(self, msg_id: str, payload: dict, timeout: float) -> dict:
        loop = asyncio.get_running_loop()
        resp_future: asyncio.Future = loop.create_future()
        self.pending_responses[msg_id] = resp_future

        raw_json = json.dumps(payload, ensure_ascii=False)
        # Broadcast to all connected extension clients
        tasks = [client.send(raw_json) for client in list(self.connected_clients)]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        try:
            result = await asyncio.wait_for(resp_future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            self.pending_responses.pop(msg_id, None)
            return {"status": "timeout", "message": "Eklentiden yanıt gelmedi"}

    def stop(self) -> None:
        """Stops the bridge server cleanly."""
        if not self.is_running:
            return
        self.is_running = False
        if self.loop and self.stop_event:
            self.loop.call_soon_threadsafe(self.stop_event.set)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)



# Global singleton instance for easy access
web_bridge = WebBridgeServer()
