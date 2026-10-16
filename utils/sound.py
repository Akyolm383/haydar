"""
Sound feedback module for Haydar.
Silenced by user preference - all audio cues are disabled in favor of visual Dynamic Island animations.
"""

class SoundFeedback:
    def __init__(self, enabled: bool = False):
        self.enabled = False

    def play_listening(self):
        """Silenced."""
        pass

    def play_success(self):
        """Silenced."""
        pass

    def play_unrecognized(self):
        """Silenced."""
        pass
