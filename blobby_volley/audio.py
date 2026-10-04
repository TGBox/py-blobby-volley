"""Procedural retro audio synthesis using Python standard library and pygame.mixer."""

import math
import struct
from typing import Dict, Optional
import pygame


class SoundManager:
    """Manages procedural retro sound effects synthesized in memory."""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.enabled = False
        self.sounds: Dict[str, pygame.mixer.Sound] = {}

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(sample_rate, -16, 1, 512)
            self._generate_all_sounds()
            self.enabled = True
        except Exception:
            # ponytail: headless or no audio device fallback, silent fail is better than crash
            self.enabled = False

    def _generate_sound(self, samples: list[float]) -> Optional[pygame.mixer.Sound]:
        """Pack normalized float samples [-1.0, 1.0] into 16-bit PCM bytes."""
        try:
            raw_bytes = bytearray()
            for s in samples:
                clamped = max(-1.0, min(1.0, s))
                val = int(clamped * 32767)
                raw_bytes.extend(struct.pack("<h", val))
            return pygame.mixer.Sound(buffer=bytes(raw_bytes))
        except Exception:
            return None

    def _generate_all_sounds(self) -> None:
        sr = self.sample_rate

        # 1. Blob hit sound: Punchy blip with rapid downward pitch sweep
        hit_samples: list[float] = []
        duration = 0.09
        num_samples = int(sr * duration)
        for i in range(num_samples):
            t = i / sr
            progress = i / num_samples
            freq = 420.0 - (progress * 260.0)
            phase = 2.0 * math.pi * freq * t
            decay = math.exp(-progress * 6.0)
            hit_samples.append(math.sin(phase) * decay * 0.8)
        s_hit = self._generate_sound(hit_samples)
        if s_hit:
            self.sounds["hit"] = s_hit

        # 2. Bounce sound: Softer hollow thump
        bounce_samples: list[float] = []
        duration = 0.12
        num_samples = int(sr * duration)
        for i in range(num_samples):
            t = i / sr
            progress = i / num_samples
            freq = 190.0 - (progress * 80.0)
            phase = 2.0 * math.pi * freq * t
            decay = math.exp(-progress * 5.0)
            bounce_samples.append(math.sin(phase) * decay * 0.7)
        s_bounce = self._generate_sound(bounce_samples)
        if s_bounce:
            self.sounds["bounce"] = s_bounce

        # 3. Whistle sound: Dual tone trill (like referee whistle)
        whistle_samples: list[float] = []
        duration = 0.22
        num_samples = int(sr * duration)
        for i in range(num_samples):
            t = i / sr
            progress = i / num_samples
            tremolo = 1.0 + 0.3 * math.sin(2.0 * math.pi * 35.0 * t)
            tone1 = math.sin(2.0 * math.pi * 2100.0 * t)
            tone2 = math.sin(2.0 * math.pi * 2350.0 * t)
            env = math.sin(progress * math.pi)
            whistle_samples.append((tone1 + tone2) * 0.35 * tremolo * env)
        s_whistle = self._generate_sound(whistle_samples)
        if s_whistle:
            self.sounds["whistle"] = s_whistle

        # 4. Score chime: Rising two-note cheer
        score_samples: list[float] = []
        duration = 0.35
        num_samples = int(sr * duration)
        for i in range(num_samples):
            t = i / sr
            progress = i / num_samples
            freq = 523.25 if progress < 0.45 else 783.99  # C5 then G5
            phase = 2.0 * math.pi * freq * t
            decay = math.exp(-((progress % 0.45) * 5.0))
            score_samples.append(math.sin(phase) * decay * 0.6)
        s_score = self._generate_sound(score_samples)
        if s_score:
            self.sounds["score"] = s_score

    def play(self, name: str) -> None:
        """Play a sound effect by name."""
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass
