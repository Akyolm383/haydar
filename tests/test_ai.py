from core.ai import GeminiAssistant


def test_quick_local_fallbacks():
    ai = GeminiAssistant(api_key=None)

    res_time = ai.answer("saat kaç")
    assert "saat" in res_time.lower()

    res_date = ai.answer("bugün günlerden ne")
    assert any(day in res_date for day in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])

    res_mood = ai.answer("nasılsın")
    assert "kral" in res_mood

    res_thanks = ai.answer("sağ ol")
    assert "rica" in res_thanks.lower()


def test_no_api_key_prompt(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    ai = GeminiAssistant(api_key=None)
    # If client is not initialized, returns prompt to add key to .env
    if not ai.client:
        res = ai.answer("kuantum fiziği nedir")
        assert ".env" in res or "GEMINI_API_KEY" in res


def test_resolve_api_key_from_env(monkeypatch):
    from core.ai import resolve_api_key
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_12345")
    assert resolve_api_key() == "test_key_12345"

