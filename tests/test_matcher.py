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


def test_extract_window_number():
    from core.matcher import extract_window_number

    assert extract_window_number("5. pencere") == 5
    assert extract_window_number("5. pencereye geç") == 5
    assert extract_window_number("5") == 5
    assert extract_window_number("beşinci pencere") == 5
    assert extract_window_number("beşinci") == 5
    assert extract_window_number("ikinci pencere") == 2
    assert extract_window_number("ilk pencere") == 1
    assert extract_window_number("10. pencere") == 10
    assert extract_window_number("üçüncü pencereye geç") == 3
    assert extract_window_number("geçersiz cümle") is None
    assert extract_window_number("") is None


def test_window_switcher_command(actual_config):
    matcher = CommandMatcher(actual_config)

    res1 = matcher.find_match("haydar pencere değiştir")
    assert res1.matched is True
    assert res1.command["id"] == "switch_window_mode"

    res2 = matcher.find_match("haydar pencereleri göster")
    assert res2.matched is True
    assert res2.command["id"] == "switch_window_mode"

    res3 = matcher.find_match("haydar alt tab")
    assert res3.matched is True
    assert res3.command["id"] == "switch_window_mode"

    res4 = matcher.find_match("haydar pencere seç")
    assert res4.matched is True
    assert res4.command["id"] == "switch_window_mode"


def test_extract_browser_click_target():
    from core.matcher import extract_browser_click_target

    assert extract_browser_click_target("tıkla abone ol") == "abone ol"
    assert extract_browser_click_target("abone ol butonuna tıkla") == "abone ol"
    assert extract_browser_click_target("sepete ekle butonuna bas") == "sepete ekle"
    assert extract_browser_click_target("tıkla sonraki sayfa") == "sonraki sayfa"
    assert extract_browser_click_target("beğen butonuna tıkla") == "beğen"
    assert extract_browser_click_target("başla tıkla") == "başla"
    assert extract_browser_click_target("masaüstüne dön") is None
    assert extract_browser_click_target("") is None


def test_browser_commands(actual_config):
    matcher = CommandMatcher(actual_config)

    res1 = matcher.find_match("haydar sonraki bölüm")
    assert res1.matched is True
    assert res1.command["id"] == "browser_next_episode"
    assert res1.command["action_type"] == "browser"

    res2 = matcher.find_match("haydar önceki bölüm")
    assert res2.matched is True
    assert res2.command["id"] == "browser_prev_episode"

    res3 = matcher.find_match("haydar introyu atla")
    assert res3.matched is True
    assert res3.command["id"] == "browser_skip_intro"

    res4 = matcher.find_match("haydar reklamı geç")
    assert res4.matched is True
    assert res4.command["id"] == "browser_skip_ad"

    res5 = matcher.find_match("haydar aşağı kaydır")
    assert res5.matched is True
    assert res5.command["id"] == "browser_scroll_down"

    res6 = matcher.find_match("haydar yukarı kaydır")
    assert res6.matched is True
    assert res6.command["id"] == "browser_scroll_up"


def test_continuous_listening_toggle_activation(actual_config):
    """Tests toggling continuous listening on and off with and without wake word."""
    matcher = CommandMatcher(actual_config)
    assert matcher.wake_word_enabled is True

    # 1. Enable continuous listening with wake word: "Haydar dinle"
    res_on = matcher.find_match("haydar dinle")
    assert res_on.matched is True
    assert res_on.command["id"] == "enable_continuous_listening"
    assert res_on.command["action_type"] == "toggle_listen_on"

    # 2. Enable continuous listening with "Haydar sürekli dinle"
    res_on2 = matcher.find_match("haydar sürekli dinle")
    assert res_on2.matched is True
    assert res_on2.command["id"] == "enable_continuous_listening"

    # 3. Direct trigger: "dinle" and "sürekli dinle" without Haydar
    res_on3 = matcher.find_match("dinle")
    assert res_on3.matched is True
    assert res_on3.command["id"] == "enable_continuous_listening"

    res_on4 = matcher.find_match("sürekli dinle")
    assert res_on4.matched is True
    assert res_on4.command["id"] == "enable_continuous_listening"

    # 4. Disable continuous listening with wake word: "Haydar dinleme"
    res_off = matcher.find_match("haydar dinleme")
    assert res_off.matched is True
    assert res_off.command["id"] == "disable_continuous_listening"
    assert res_off.command["action_type"] == "toggle_listen_off"

    # 5. Direct trigger: "dinleme" without Haydar
    res_off2 = matcher.find_match("dinleme")
    assert res_off2.matched is True
    assert res_off2.command["id"] == "disable_continuous_listening"

    # 6. In continuous mode: commands work without Haydar, and 'dinleme' switches it off
    matcher.wake_word_enabled = False

    res_cmd = matcher.find_match("sesi aç")
    assert res_cmd.matched is True
    assert res_cmd.command["id"] == "volume_up"

    res_stop = matcher.find_match("dinlemeyi durdur")
    assert res_stop.matched is True
    assert res_stop.command["id"] == "disable_continuous_listening"





