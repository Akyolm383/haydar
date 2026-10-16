import math
import struct
from typing import Callable, Optional
import speech_recognition as sr

try:
    import audioop
except ImportError:
    audioop = None


def calculate_rms(data: bytes, sample_width: int) -> int:
    """Calculates RMS audio energy."""
    if not data:
        return 0
    if audioop is not None:
        try:
            return audioop.rms(data, sample_width)
        except Exception:
            pass

    # Pure Python fallback for RMS
    count = len(data) // sample_width
    if count == 0:
        return 0
    fmt = "%dh" % count if sample_width == 2 else "%db" % count
    try:
        shorts = struct.unpack(fmt, data[: count * sample_width])
        sum_squares = sum(s * s for s in shorts)
        return int(math.sqrt(sum_squares / count))
    except Exception:
        return 0


class StreamProxy:
    def __init__(
        self,
        stream,
        sample_width: int,
        threshold: float,
        on_speech_start: Optional[Callable[[], None]],
        on_audio_level: Optional[Callable[[float], None]] = None,
    ):
        self._stream = stream
        self._sample_width = sample_width
        self._threshold = threshold
        self._on_speech_start = on_speech_start
        self._on_audio_level = on_audio_level
        self._speech_triggered = False

    def read(self, size):
        data = self._stream.read(size)
        if data:
            energy = calculate_rms(data, self._sample_width)
            if self._on_audio_level:
                # Normalize amplitude between 0.0 and 1.0
                norm_level = min(1.0, max(0.0, energy / max(100.0, self._threshold * 2.5)))
                try:
                    self._on_audio_level(norm_level)
                except Exception:
                    pass

            if not self._speech_triggered:
                if energy > (self._threshold * 1.1):
                    self._speech_triggered = True
                    if self._on_speech_start:
                        try:
                            self._on_speech_start()
                        except Exception:
                            pass
        return data

    def __getattr__(self, name):
        return getattr(self._stream, name)


class VoiceListener:
    def __init__(
        self,
        language: str = "tr-TR",
        energy_threshold_adjustment: bool = True,
        on_listening_start: Optional[Callable[[], None]] = None,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_speech_detected: Optional[Callable[[], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
    ):
        self.language = language
        self.energy_threshold_adjustment = energy_threshold_adjustment
        self.on_listening_start = on_listening_start
        self.on_speech_start = on_speech_start
        self.on_speech_detected = on_speech_detected
        self.on_audio_level = on_audio_level

        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8
        self.recognizer.non_speaking_duration = 0.5
        self.recognizer.dynamic_energy_threshold = True

        self.microphone = sr.Microphone()

    def calibrate(self, duration: float = 1.0):
        """Calibrates microphone for ambient room noise."""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)

    def listen_once(self, timeout: Optional[float] = None, phrase_time_limit: float = 7.0) -> Optional[str]:
        """
        Listens for a single speech phrase and transcribes it via Google Speech API.
        Returns the recognized string, or None if no speech / error.
        """
        if self.on_listening_start:
            self.on_listening_start()

        try:
            with self.microphone as source:
                original_stream = source.stream
                source.stream = StreamProxy(
                    stream=original_stream,
                    sample_width=source.SAMPLE_WIDTH,
                    threshold=self.recognizer.energy_threshold,
                    on_speech_start=self.on_speech_start,
                    on_audio_level=self.on_audio_level,
                )

                try:
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit,
                    )
                finally:
                    source.stream = original_stream

            if self.on_speech_detected:
                self.on_speech_detected()

            # Transcribe with Google Speech Recognition
            text = self.recognizer.recognize_google(audio, language=self.language)
            return text

        except sr.WaitTimeoutError:
            # Silence timeout, normal in continuous loop
            return None
        except sr.UnknownValueError:
            # Audio was received but Google couldn't understand it
            return ""
        except sr.RequestError as e:
            # Network issue or Google API unavailable
            raise RuntimeError(f"Google Speech API bağlantı hatası: {e}")
