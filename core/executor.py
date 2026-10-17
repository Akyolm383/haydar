import os
import subprocess
import time
from typing import Any, Dict, List, Optional
import pyautogui

from core.web_bridge import web_bridge

# Disable PyAutoGUI corner failsafe so parked cursor in full-screen doesn't abort voice commands
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05


class ActionExecutor:
    def __init__(self, cooldown_seconds: float = 0.8):
        self.cooldown_seconds = cooldown_seconds
        self.last_execution_time = 0.0
        self.last_command_id: Optional[str] = None

    def execute(self, command: Dict[str, Any]) -> bool:
        """
        Executes the action defined in the command configuration.
        Returns True if executed, False if skipped due to cooldown or error.
        """
        now = time.time()
        cmd_id = command.get("id", "unknown")

        # Debounce/cooldown check for the same command or general flood prevention
        if (now - self.last_execution_time) < self.cooldown_seconds:
            return False

        action_type = command.get("action_type", "press")
        keys = command.get("keys", [])
        repeat = int(command.get("repeat", 1))

        try:
            if action_type == "hotkey":
                # Multi-key combination, e.g. ['win', 'd'] or ['alt', 'f4']
                self._execute_hotkey(keys)
            elif action_type == "press":
                # Single key pressed multiple times, e.g. ['right'] or ['volumeup']
                self._execute_press(keys, repeat)
            elif action_type == "write":
                text = command.get("text", "")
                if text:
                    pyautogui.write(text, interval=0.02)
            elif action_type == "run":
                command_str = command.get("command", "")
                if command_str:
                    subprocess.Popen(command_str, shell=True)
            elif action_type == "open":
                target = command.get("target", "")
                if target:
                    os.startfile(target)
            elif action_type == "window_switcher":
                return self.open_window_switcher()
            elif action_type == "browser":
                result = self.execute_browser_action(command)
                self.last_execution_time = time.time()
                self.last_command_id = cmd_id
                return result.get("status") == "success"
            elif action_type == "exit":
                if hasattr(self, "on_exit_callback") and self.on_exit_callback:
                    self.on_exit_callback()
                return True
            elif action_type in ("toggle_listen_on", "toggle_listen_off"):
                self.last_execution_time = time.time()
                self.last_command_id = cmd_id
                return True
            elif action_type == "none":
                return True
            else:
                return False

            self.last_execution_time = time.time()
            self.last_command_id = cmd_id
            return True

        except Exception as e:
            print(f"[Executor Hatası] Komut çalıştırılamadı ({cmd_id}): {e}")
            return False

    def open_window_switcher(self) -> bool:
        """Opens persistent Alt+Tab window switcher in Windows."""
        try:
            pyautogui.hotkey("ctrl", "alt", "tab")
            return True
        except Exception as e:
            print(f"[Switcher Hatası] {e}")
            return False

    def close_window_switcher(self):
        """Closes Alt+Tab window switcher cleanly."""
        try:
            pyautogui.press("escape")
        except Exception:
            pass

    def switch_to_nth_window(self, index: int) -> bool:
        """
        Switches directly to the N-th window in the z-order stack using Alt+Tab.
        index: 1-indexed (e.g. 1, 2, 3, 4, 5...)
        """
        try:
            if index < 1:
                index = 1
            # Send escape in case persistent switcher overlay is open
            pyautogui.press("escape")
            time.sleep(0.04)

            # Hold down Alt, press Tab N times, release Alt
            pyautogui.keyDown("alt")
            time.sleep(0.04)
            for _ in range(index):
                pyautogui.press("tab")
                time.sleep(0.05)
            time.sleep(0.06)
            pyautogui.keyUp("alt")
            return True
        except Exception as e:
            print(f"[Switch Window Hatası] {e}")
            try:
                pyautogui.keyUp("alt")
            except Exception:
                pass
            return False

    def execute_browser_action(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches browser DOM automation command to Haydar Web Bridge."""
        browser_action = command.get("browser_action", "click_button")
        target = command.get("target", "")
        params = command.get("params", {})
        return web_bridge.send_command(action=browser_action, target=target, params=params)

    def browser_click_custom(self, target: str) -> Dict[str, Any]:
        """Clicks a dynamically extracted target text in active browser tab."""
        return web_bridge.send_command(action="click_button", target=target)

    def browser_scroll(self, direction: str = "down") -> Dict[str, Any]:
        """Scrolls active browser tab up or down."""
        action = "scroll_down" if direction == "down" else "scroll_up"
        return web_bridge.send_command(action=action)

    def _execute_hotkey(self, keys: List[str]):
        """Executes a hotkey sequence."""
        if not keys:
            return
        
        # Mapping windows key alias
        mapped_keys = [self._map_key(k) for k in keys]
        pyautogui.hotkey(*mapped_keys)

    def _execute_press(self, keys: List[str], repeat: int):
        """Executes key presses."""
        if not keys:
            return
        
        for _ in range(repeat):
            for k in keys:
                mapped = self._map_key(k)
                pyautogui.press(mapped)
                if repeat > 1:
                    time.sleep(0.04)

    @staticmethod
    def _map_key(key: str) -> str:
        """Maps user-friendly key names to pyautogui recognized key strings."""
        k = key.lower().strip()
        key_map = {
            "win": "winleft",
            "windows": "winleft",
            "super": "winleft",
            "ctrl": "ctrlleft",
            "control": "ctrlleft",
            "alt": "altleft",
            "shift": "shiftleft",
            "enter": "enter",
            "return": "enter",
            "esc": "escape",
            "escape": "escape",
            "space": "space",
            "boşluk": "space",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "yukarı": "up",
            "aşağı": "down",
            "sol": "left",
            "sağ": "right",
            "volup": "volumeup",
            "voldown": "volumedown",
            "mute": "volumemute",
            "volumeup": "volumeup",
            "volumedown": "volumedown",
            "volumemute": "volumemute",
        }
        return key_map.get(k, k)
