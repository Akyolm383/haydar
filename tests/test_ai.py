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


def test_no_api_key_prompt():
    ai = GeminiAssistant(api_key=None)
    res = ai.answer("kuantum fiziği nedir")
    assert "commands.json" in res
