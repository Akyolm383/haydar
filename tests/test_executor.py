import time
from unittest.mock import MagicMock, patch
import pytest
from core.executor import ActionExecutor


def test_map_key_aliases():
    assert ActionExecutor._map_key("win") == "winleft"
    assert ActionExecutor._map_key("windows") == "winleft"
    assert ActionExecutor._map_key("super") == "winleft"
    assert ActionExecutor._map_key("ctrl") == "ctrlleft"
    assert ActionExecutor._map_key("alt") == "altleft"
    assert ActionExecutor._map_key("shift") == "shiftleft"
    assert ActionExecutor._map_key("esc") == "escape"
    assert ActionExecutor._map_key("escape") == "escape"
    assert ActionExecutor._map_key("space") == "space"
    assert ActionExecutor._map_key("boşluk") == "space"
    assert ActionExecutor._map_key("bosluk") == "space"
    assert ActionExecutor._map_key("tab") == "tab"
    assert ActionExecutor._map_key("sekme") == "tab"
    assert ActionExecutor._map_key("sil") == "backspace"
    assert ActionExecutor._map_key("backspace") == "backspace"
    assert ActionExecutor._map_key("yukarı") == "up"
    assert ActionExecutor._map_key("aşağı") == "down"
    assert ActionExecutor._map_key("sol") == "left"
    assert ActionExecutor._map_key("sağ") == "right"
    assert ActionExecutor._map_key("mute") == "volumemute"


def test_cooldown_mechanism():
    executor = ActionExecutor(cooldown_seconds=0.5)

    with patch("pyautogui.press") as mock_press:
        cmd = {"id": "test_press", "action_type": "press", "keys": ["f"]}

        # First execution must succeed
        res1 = executor.execute(cmd)
        assert res1 is True
        assert mock_press.call_count == 1

        # Immediate second execution within cooldown must be debounced/skipped
        res2 = executor.execute(cmd)
        assert res2 is False
        assert mock_press.call_count == 1

        # After cooldown passes, execution must succeed again
        time.sleep(0.55)
        res3 = executor.execute(cmd)
        assert res3 is True
        assert mock_press.call_count == 2


def test_execute_hotkey():
    executor = ActionExecutor(cooldown_seconds=0.0)

    with patch("pyautogui.hotkey") as mock_hotkey:
        cmd = {"id": "test_hotkey", "action_type": "hotkey", "keys": ["ctrl", "t"]}
        res = executor.execute(cmd)
        assert res is True
        mock_hotkey.assert_called_once_with("ctrlleft", "t")


def test_execute_exit_callback():
    executor = ActionExecutor(cooldown_seconds=0.0)
    mock_exit = MagicMock()
    executor.on_exit_callback = mock_exit

    cmd = {"id": "exit_haydar", "action_type": "exit"}
    res = executor.execute(cmd)
    assert res is True
    mock_exit.assert_called_once()


def test_unknown_action_type():
    executor = ActionExecutor(cooldown_seconds=0.0)
    cmd = {"id": "invalid", "action_type": "nonexistent_action"}
    res = executor.execute(cmd)
    assert res is False
