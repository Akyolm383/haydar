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


def test_gemini_query_extraction(actual_config):
    from core.matcher import extract_gemini_query

    # Direct questions with 'gemini'
    is_gem, q = extract_gemini_query("gemini saat kaç")
    assert is_gem is True
    assert q == "saat kaç"

    # Phonetic Turkish transcription 'cemini'
    is_gem2, q2 = extract_gemini_query("cemini gökyüzü neden mavi")
    assert is_gem2 is True
    assert q2 == "gökyüzü neden mavi"

    # Standalone 'gemini' for waiting mode
    is_gem3, q3 = extract_gemini_query("gemini")
    assert is_gem3 is True
    assert q3 == ""

    # Conversational wake greeting phrases: 'gemini dinle', 'cemil dinle', 'hey gemini'
    is_gem_dinle, q_dinle = extract_gemini_query("gemini dinle")
    assert is_gem_dinle is True
    assert q_dinle == ""

    is_gem_cemil, q_cemil = extract_gemini_query("cemil dinle")
    assert is_gem_cemil is True
    assert q_cemil == ""

    is_gem_hey, q_hey = extract_gemini_query("hey gemini")
    assert is_gem_hey is True
    assert q_hey == ""

    is_gem_merhaba, q_merhaba = extract_gemini_query("merhaba gemini")
    assert is_gem_merhaba is True
    assert q_merhaba == ""

    # 'geminiye sor ...'
    is_gem4, q4 = extract_gemini_query("geminiye sor yarın hava nasıl")
    assert is_gem4 is True
    assert q4 == "yarın hava nasıl"

    # 'haydar' commands must NEVER match gemini
    is_gem5, _ = extract_gemini_query("haydar 15 saniye ileri sar")
    assert is_gem5 is False

    is_gem6, _ = extract_gemini_query("haydar saat kaç")
    assert is_gem6 is False


def test_spotify_commands(actual_config):
    matcher = CommandMatcher(actual_config)

    # Spotify play/pause
    res_pause = matcher.find_match("haydar şarkıyı durdur")
    assert res_pause.matched is True
    assert res_pause.command["id"] == "spotify_play_pause"

    res_play = matcher.find_match("haydar müzik çal")
    assert res_play.matched is True
    assert res_play.command["id"] == "spotify_play_pause"

    res_spot_pause = matcher.find_match("haydar spotify durdur")
    assert res_spot_pause.matched is True
    assert res_spot_pause.command["id"] == "spotify_play_pause"

    res_spot_play = matcher.find_match("haydar spotify çal")
    assert res_spot_play.matched is True
    assert res_spot_play.command["id"] == "spotify_play_pause"

    # 'müziği kapat' must trigger spotify_play_pause, NEVER exit_haydar!
    res_music_kapat = matcher.find_match("haydar müziği kapat")
    assert res_music_kapat.matched is True
    assert res_music_kapat.command["id"] == "spotify_play_pause"

    res_sarki_kapat = matcher.find_match("haydar şarkıyı kapat")
    assert res_sarki_kapat.matched is True
    assert res_sarki_kapat.command["id"] == "spotify_play_pause"

    # Next / Prev track
    res_next = matcher.find_match("haydar sonraki şarkı")
    assert res_next.matched is True
    assert res_next.command["id"] == "spotify_next_track"

    # 'şarkı değiştir' must trigger spotify_next_track, NEVER switch_window!
    res_change1 = matcher.find_match("haydar şarkı değiştir")
    assert res_change1.matched is True
    assert res_change1.command["id"] == "spotify_next_track"

    res_change2 = matcher.find_match("haydar müzik değiştir")
    assert res_change2.matched is True
    assert res_change2.command["id"] == "spotify_next_track"

    res_skip = matcher.find_match("haydar şarkıyı atla")
    assert res_skip.matched is True
    assert res_skip.command["id"] == "spotify_next_track"

    res_prev = matcher.find_match("haydar önceki şarkı")
    assert res_prev.matched is True
    assert res_prev.command["id"] == "spotify_prev_track"

    # Shuffle / Repeat / Like / Open
    res_shuffle = matcher.find_match("haydar karışık çal")
    assert res_shuffle.matched is True
    assert res_shuffle.command["id"] == "spotify_shuffle"

    res_like = matcher.find_match("haydar şarkıyı beğen")
    assert res_like.matched is True
    assert res_like.command["id"] == "spotify_like"

    res_open = matcher.find_match("haydar spotify aç")
    assert res_open.matched is True
    assert res_open.command["id"] == "spotify_open"

    res_open_phonetic = matcher.find_match("haydar spotifayı aç")
    assert res_open_phonetic.matched is True
    assert res_open_phonetic.command["id"] == "spotify_open"

    # Exit Haydar
    res_exit = matcher.find_match("haydar asistanı kapat")
    assert res_exit.matched is True
    assert res_exit.command["id"] == "exit_haydar"


