import json
import os
import pytest


def test_commands_json_structure():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "commands.json")
    assert os.path.exists(config_path), "commands.json does not exist"

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "settings" in data
    assert "commands" in data
    assert isinstance(data["commands"], list)
    assert len(data["commands"]) > 0

    valid_actions = {"hotkey", "press", "write", "run", "open", "exit", "window_switcher", "browser"}

    for cmd in data["commands"]:
        assert "id" in cmd, f"Missing id in command: {cmd}"
        assert "triggers" in cmd, f"Missing triggers in command: {cmd}"
        assert len(cmd["triggers"]) > 0, f"Empty triggers in command: {cmd['id']}"
        assert "action_type" in cmd, f"Missing action_type in command: {cmd['id']}"
        assert cmd["action_type"] in valid_actions, f"Invalid action_type: {cmd['action_type']}"
        if cmd["action_type"] in ("hotkey", "press"):
            assert "keys" in cmd, f"Missing keys in command: {cmd['id']}"
            assert len(cmd["keys"]) > 0, f"Empty keys in command: {cmd['id']}"
