import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from rapidfuzz import fuzz


TURKISH_NUMBERS = {
    "on beş": "15",
    "onbeş": "15",
    "on bir": "11",
    "on iki": "12",
    "on üç": "13",
    "on dört": "14",
    "on altı": "16",
    "on yedi": "17",
    "on sekiz": "18",
    "on dokuz": "19",
    "on": "10",
    "yirmi": "20",
    "otuz": "30",
    "kırk": "40",
    "elli": "50",
    "altmış": "60",
    "sıfır": "0",
    "bir": "1",
    "iki": "2",
    "üç": "3",
    "dört": "4",
    "beş": "5",
    "altı": "6",
    "yedi": "7",
    "sekiz": "8",
    "dokuz": "9",
}


def normalize_turkish(text: str) -> str:
    """
    Turkish-aware text normalization.
    Converts uppercase Turkish letters correctly, normalizes number words to digits,
    and removes punctuation.
    """
    if not text:
        return ""
    
    # Proper Turkish uppercase to lowercase conversion
    mapping = {
        "İ": "i",
        "I": "ı",
        "Ğ": "ğ",
        "Ü": "ü",
        "Ş": "ş",
        "Ö": "ö",
        "Ç": "ç",
    }
    for upper, lower in mapping.items():
        text = text.replace(upper, lower)
    text = text.lower()
    
    # Remove punctuation and special characters
    text = re.sub(r"[^\w\s\dçğıöşü]", " ", text)

    # Convert spoken Turkish number words to digits
    for word, digit in sorted(TURKISH_NUMBERS.items(), key=lambda x: -len(x[0])):
        text = re.sub(r"\b" + re.escape(word) + r"\b", digit, text)

    # Collapse multiple whitespaces into one
    text = re.sub(r"\s+", " ", text).strip()
    return text


@dataclass
class MatchResult:
    matched: bool
    command: Optional[Dict[str, Any]] = None
    matched_trigger: str = ""
    score: float = 0.0
    processed_text: str = ""
    reason: str = ""


GEMINI_TRIGGERS = [
    "gemini",
    "cemini",
    "ceminay",
    "geminay",
    "cimini",
    "gimini",
    "cimine",
    "cebini",
    "cemil",
    "yapay zeka",
]


def extract_gemini_query(text: str) -> Tuple[bool, str]:
    """
    Checks if speech input is addressed to Gemini AI.
    Handles Turkish speech recognition phonetic variations:
    - 'gemi ne', 'gemi ni', 'gemı ne', 'gemı ni'
    - 'gemini', 'gemine', 'geminay', 'cemini', 'cemil'
    - 'ge mi ne', 'yapay zeka'
    """
    normalized = normalize_turkish(text)
    words = normalized.split()
    if not words:
        return False, ""

    # Optional greeting prefixes like 'hey', 'ey', 'alo', 'merhaba', 'selam', 'ya'
    if words[0] in ("hey", "ey", "alo", "merhaba", "selam", "ya") and len(words) > 1:
        words = words[1:]

    # Normalized phonetic words where dotless ı -> i
    i_words = [w.replace("ı", "i") for w in words]
    wake_len = 0

    # 3-word trigger: 'ge mi ne', 'ge mi ni'
    if len(i_words) >= 3 and i_words[0] == "ge" and i_words[1] == "mi" and i_words[2] in ("ne", "ni"):
        wake_len = 3
    # 2-word triggers: 'gemi ne', 'gemi ni', 'cemi ne', 'cemi ni', 'yapay zeka'
    elif len(i_words) >= 2 and (
        (i_words[0] in ("gemi", "cemi", "cami", "camı") and i_words[1] in ("ne", "ni", "nin", "ye", "de"))
        or (i_words[0] == "yapay" and i_words[1] in ("zeka", "zekaya", "zekam"))
    ):
        wake_len = 2
    else:
        # 1-word triggers
        single_triggers = {
            "gemini", "gemine", "geminay", "geminiye", "cemini", "ceminay",
            "cemine", "cemil", "cemile", "gimini", "cimini", "cebini", "camini",
            "gemi", "cemi"
        }
        for idx in range(min(2, len(i_words))):
            w = i_words[idx]
            if w in single_triggers or fuzz.ratio(w, "gemini") >= 72 or fuzz.ratio(w, "geminay") >= 75:
                wake_len = idx + 1
                break

    if wake_len == 0:
        return False, ""

    # Query is everything after the wake phrase
    remaining_words = words[wake_len:]
    remaining = " ".join(remaining_words).strip()

    # Strip conversational filler greetings
    filler_words = (
        "dinle", "dinliyor musun", "bakar misin", "bakar mısın",
        "burada misin", "burada mısın", "sor", "soru", "efendim", "alo", "baksana"
    )
    for filler in filler_words:
        if remaining == filler:
            remaining = ""
            break
        elif remaining.startswith(filler + " "):
            remaining = remaining[len(filler):].strip()

    return True, remaining


class CommandMatcher:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.settings = config.get("settings", {})
        self.commands: List[Dict[str, Any]] = config.get("commands", [])
        self.default_threshold: float = float(self.settings.get("default_threshold", 70))
        self.wake_word_enabled: bool = bool(self.settings.get("wake_word_enabled", False))
        self.wake_word: str = normalize_turkish(self.settings.get("wake_word", "haydar"))

    def extract_gemini_query(self, text: str) -> Tuple[bool, str]:
        """Extracts Gemini query if addressed to Gemini."""
        return extract_gemini_query(text)

    def reload_config(self, config: Dict[str, Any]):
        """Reloads configuration and commands."""
        self.__init__(config)

    def extract_command_text(self, text: str) -> Tuple[str, bool]:
        """
        Extracts command text by handling wake word if enabled.
        Returns (extracted_text, wake_word_found).
        """
        normalized = normalize_turkish(text)
        if not self.wake_word_enabled:
            return normalized, True

        words = normalized.split()
        if not words:
            return "", False

        # Check if wake word is present
        # e.g., 'haydar masaüstüne dön' or 'hey haydar videoyu durdur'
        wake_idx = -1
        for i, word in enumerate(words):
            score = fuzz.ratio(word, self.wake_word)
            if score >= 80:
                wake_idx = i
                break

        if wake_idx != -1:
            # Command is everything after the wake word
            remaining_words = words[wake_idx + 1 :]
            command_text = " ".join(remaining_words).strip()
            return command_text, True

        return normalized, False

    def find_match(self, raw_text: str) -> MatchResult:
        """
        Finds the best matching command for the given recognized text.
        """
        if not raw_text or not raw_text.strip():
            return MatchResult(matched=False, reason="Boş ses girdisi")

        processed_text, wake_detected = self.extract_command_text(raw_text)

        if self.wake_word_enabled and not wake_detected:
            return MatchResult(
                matched=False,
                processed_text=processed_text,
                reason=f"Uyandırma kelimesi ({self.wake_word}) algılanmadı",
            )

        if not processed_text:
            return MatchResult(
                matched=True,
                command={
                    "id": "wake_greeting",
                    "description": "Efendim? Dinliyorum...",
                    "action_type": "none",
                    "keys": [],
                },
                matched_trigger=self.wake_word,
                score=100.0,
                processed_text=self.wake_word,
                reason="Uyandırma kelimesi algılandı",
            )

        best_command: Optional[Dict[str, Any]] = None
        best_trigger = ""
        best_score = 0.0

        in_nums = set(re.findall(r"\b\d+\b", processed_text))

        for cmd in self.commands:
            threshold = float(cmd.get("threshold", self.default_threshold))
            triggers = cmd.get("triggers", [])

            for trigger in triggers:
                norm_trigger = normalize_turkish(trigger)
                tr_nums = set(re.findall(r"\b\d+\b", norm_trigger))

                # Number conflict check:
                # 1. If both specify numbers and they differ (e.g. 15 vs 5), do not match
                if in_nums and tr_nums and in_nums != tr_nums:
                    continue

                # 2. If trigger explicitly requires a number (e.g. '15 saniye') but input doesn't provide one, skip
                if tr_nums and not in_nums:
                    continue

                # 3. If input specifies a number but trigger has none (e.g. '15 saniye ileri' vs 'ileriye sar'),
                # penalize generic trigger so specific numbered trigger wins
                penalty = 35.0 if (in_nums and not tr_nums) else 0.0

                # Proportional penalty when word count differs
                len_diff = abs(len(norm_trigger.split()) - len(processed_text.split()))
                word_penalty = len_diff * 6.0

                token_set_score = fuzz.token_set_ratio(processed_text, norm_trigger)
                full_ratio = fuzz.ratio(processed_text, norm_trigger)

                # Prioritize exact or near-identical string matches
                if processed_text == norm_trigger:
                    score = 100.0
                elif full_ratio >= 90:
                    score = full_ratio
                else:
                    raw_score = max(token_set_score * 0.7 + full_ratio * 0.3, full_ratio)
                    score = max(0.0, raw_score - penalty - word_penalty)

                if score > best_score:
                    best_score = score
                    best_command = cmd
                    best_trigger = trigger

        if best_command is not None:
            cmd_threshold = float(best_command.get("threshold", self.default_threshold))
            if best_score >= cmd_threshold:
                return MatchResult(
                    matched=True,
                    command=best_command,
                    matched_trigger=best_trigger,
                    score=best_score,
                    processed_text=processed_text,
                    reason="Eşleşme başarılı",
                )
            else:
                return MatchResult(
                    matched=False,
                    command=best_command,
                    matched_trigger=best_trigger,
                    score=best_score,
                    processed_text=processed_text,
                    reason=f"Benzerlik skoru eşiğin altında kaldı ({best_score:.1f} < {cmd_threshold})",
                )

        return MatchResult(
            matched=False,
            processed_text=processed_text,
            reason="Tanımlı komutlarla eşleşmedi",
        )
