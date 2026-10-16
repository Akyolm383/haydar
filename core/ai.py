import datetime
import os
import re
from typing import Optional

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class GeminiAssistant:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.client = None
        if HAS_GENAI and self.api_key and self.api_key.strip():
            try:
                self.client = genai.Client(api_key=self.api_key.strip())
            except Exception as e:
                print(f"[Gemini Başlatma Hatası] {e}")

    def reload_key(self, api_key: Optional[str]):
        self.__init__(api_key)

    def answer(self, prompt: str) -> str:
        """
        Answers a user query concisely for the Dynamic Island display.
        """
        norm_prompt = prompt.lower().strip()

        # 1. Quick Local Fallbacks (Zero-latency instant responses)
        if any(w in norm_prompt for w in ["saat kaç", "saati söyle", "zaman", "saat"]):
            now = datetime.datetime.now()
            return f"Şu an saat {now.strftime('%H:%M')}."

        if any(w in norm_prompt for w in ["bugün ayın kaçı", "tarih ne", "tarih", "hangi gündeyiz", "hangi gün", "günlerden ne", "bugün gün"]):
            now = datetime.datetime.now()
            days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
            day_name = days[now.weekday()]
            return f"Bugün {now.day}.{now.month}.{now.year}, {day_name}."

        if any(w in norm_prompt for w in ["nasılsın", "naber", "ne haber", "nasıl gidiyor"]):
            return "İyiyim kral, seni dinliyorum! Bir komut ver emrindeyim."

        if any(w in norm_prompt for w in ["teşekkürler", "teşekkür ederim", "sağ ol", "eyvallah", "adamsın"]):
            return "Rica ederim kral, her zaman buradayım!"

        # 2. Gemini AI Query
        if not self.client:
            return "Cevaplayabilmem için commands.json'a Gemini API anahtarı ekleyin."

        try:
            sys_instruction = (
                "Sen 'Haydar' isimli Türkçe masaüstü sesli asistansın. "
                "Cevabın kullanıcının ekranının üstündeki Dinamik Ada widget'ında gösterilecek. "
                "Bu yüzden cevabın KESİNLİKLE ÇOK KISA, net, samimi ve maksimum 1-2 cümle (en fazla 25 kelime) olmalıdır. "
                "Markdown başlıkları, uzun listeler kullanma."
            )

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruction,
                    max_output_tokens=60,
                    temperature=0.7,
                ),
            )

            if response and response.text:
                clean_text = response.text.replace("\n", " ").strip()
                # Clean up any trailing quotation marks or bold markers
                clean_text = re.sub(r"[*_`]", "", clean_text)
                return clean_text

            return "Bunu tam anlayamadım, tekrar eder misiniz?"

        except Exception as e:
            return f"Yapay zeka yanıt veremedi: {str(e)[:40]}"
