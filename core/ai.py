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


def resolve_api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    """
    Safely resolves Gemini API key from multiple sources without risking git leakage:
    1. Explicitly passed key
    2. Environment variables (GEMINI_API_KEY, GOOGLE_API_KEY)
    3. .env file in root directory
    4. config/secrets.json
    """
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()

    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.environ.get(var)
        if val and val.strip():
            return val.strip()

    # Read from local .env (protected by .gitignore)
    env_path = os.path.abspath(".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                            cleaned = v.strip().strip("'\"")
                            if cleaned:
                                return cleaned
        except Exception:
            pass

    # Read from config/secrets.json (protected by .gitignore)
    secrets_path = os.path.abspath("config/secrets.json")
    if os.path.exists(secrets_path):
        try:
            import json
            with open(secrets_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                val = data.get("gemini_api_key")
                if val and str(val).strip():
                    return str(val).strip()
        except Exception:
            pass

    return None


class GeminiAssistant:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = resolve_api_key(api_key)
        self.client = None
        if HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
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
            return "Cevaplayabilmem için .env dosyasına GEMINI_API_KEY ekleyin."

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
