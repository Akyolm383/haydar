import json
import os
import pytest
from core.matcher import CommandMatcher, normalize_turkish


@pytest.fixture
def actual_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "commands.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def continuous_config(actual_config):
    cfg = json.loads(json.dumps(actual_config))
    cfg["settings"]["wake_word_enabled"] = False
    return cfg


def test_turkish_normalization():
    assert normalize_turkish("İSTANBUL") == "istanbul"
    assert normalize_turkish("IŞIK") == "ışık"
    assert normalize_turkish("Masaüstüne dön...!") == "masaüstüne dön"
    assert normalize_turkish("   videoyu    ileri    sar   ") == "videoyu ileri sar"
    # Spoken number word normalization
    assert normalize_turkish("on beş saniye") == "15 saniye"
    assert normalize_turkish("beş saniye") == "5 saniye"
    assert normalize_turkish("otuz saniye") == "30 saniye"


def test_wake_word_mode_activation(actual_config):
    """When wake word is enabled, only commands with 'Haydar' must activate."""
    matcher = CommandMatcher(actual_config)
    assert matcher.wake_word_enabled is True

    # 1. Without 'Haydar': must NOT activate
    res_no_wake = matcher.find_match("masaüstüne dön")
    assert res_no_wake.matched is False
    assert "Uyandırma kelimesi" in res_no_wake.reason

    res_no_wake2 = matcher.find_match("15 saniye ileri sar")
    assert res_no_wake2.matched is False

    # 2. With 'Haydar': must activate
    res_wake = matcher.find_match("haydar masaüstüne dön")
    assert res_wake.matched is True
    assert res_wake.command["id"] == "show_desktop"

    # 3. Just 'Haydar' greeting
    res_just_haydar = matcher.find_match("haydar")
    assert res_just_haydar.matched is True
    assert res_just_haydar.command["id"] == "wake_greeting"

    # 4. Haydar video dursun
    res_video = matcher.find_match("haydar video dursun")
    assert res_video.matched is True
    assert res_video.command["id"] == "media_play_pause"

    # 5. Haydar 15 saniye ileri sar
    res_15s = matcher.find_match("haydar 15 saniye ileri sar")
    assert res_15s.matched is True
    assert res_15s.command["id"] == "media_forward_15s"

    # 6. Haydar ses artsın
    res_ses = matcher.find_match("haydar ses artsın")
    assert res_ses.matched is True
    assert res_ses.command["id"] == "volume_up"

    # 7. Haydarı kapat
    res_exit = matcher.find_match("haydarı kapat")
    assert res_exit.matched is True
    assert res_exit.command["id"] == "exit_haydar"


def test_continuous_mode(continuous_config):
    """When wake word is disabled, commands work without saying Haydar."""
    matcher = CommandMatcher(continuous_config)
    assert matcher.wake_word_enabled is False

    res = matcher.find_match("masaüstüne dön")
    assert res.matched is True
    assert res.command["id"] == "show_desktop"

    res_15 = matcher.find_match("15 saniye ileri sar")
    assert res_15.matched is True
    assert res_15.command["id"] == "media_forward_15s"


def test_unrelated_sentence_does_not_match(actual_config):
    matcher = CommandMatcher(actual_config)
    res = matcher.find_match("bugün hava çok güzel patates kızartması")
    assert res.matched is False
