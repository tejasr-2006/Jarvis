"""Optional offline wake-word listener using Vosk and sounddevice.

The microphone is opened only after an explicit user click in the desktop UI.
A Vosk model must be downloaded by the user and its folder configured locally.
No audio is intentionally sent over the network by this module.
"""
from __future__ import annotations

import json
import os
import queue
import re

from PySide6.QtCore import QThread, Signal
from app.voice.wake_phrase import extract_command_after_wake_phrase, is_wake_phrase_only


class WakeWordListener(QThread):
    command_ready = Signal(str)
    status_changed = Signal(str)
    failed = Signal(str)

    def __init__(self, model_path: str, wake_phrase: str = "jarvis", parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.wake_phrase = wake_phrase.strip().casefold() or "jarvis"
        self._stop_requested = False
        self._audio_queue: queue.Queue[bytes] = queue.Queue(maxsize=40)

    def stop(self):
        self._stop_requested = True
        # Unblock the worker loop if it is waiting for audio.
        try:
            self._audio_queue.put_nowait(b"")
        except queue.Full:
            pass
        self.wait(3000)

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            self.status_changed.emit(f"Microphone status: {status}")
        try:
            self._audio_queue.put_nowait(bytes(indata))
        except queue.Full:
            # Drop the oldest chunk rather than allowing unbounded memory growth.
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.put_nowait(bytes(indata))
            except (queue.Empty, queue.Full):
                pass

    def run(self):
        try:
            import sounddevice as sd
            from vosk import Model, KaldiRecognizer
        except Exception as exc:
            self.failed.emit(
                "Offline voice dependencies are missing. Install requirements-voice.txt. "
                f"Details: {type(exc).__name__}"
            )
            return

        if not os.path.isdir(self.model_path):
            self.failed.emit(
                "Vosk model folder not found. Set JARVIS_VOSK_MODEL_PATH to the extracted model folder."
            )
            return

        try:
            model = Model(self.model_path)
            recognizer = KaldiRecognizer(model, 16000)
            recognizer.SetWords(False)
            awaiting_command = False
            self.status_changed.emit("Offline wake listening enabled. Say the wake phrase.")
            with sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                dtype="int16",
                channels=1,
                callback=self._audio_callback,
            ):
                while not self._stop_requested:
                    try:
                        chunk = self._audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    if self._stop_requested:
                        break
                    if not chunk:
                        continue
                    if not recognizer.AcceptWaveform(chunk):
                        continue
                    try:
                        text = json.loads(recognizer.Result()).get("text", "").strip()
                    except (ValueError, TypeError):
                        continue
                    if not text:
                        continue

                    if awaiting_command:
                        # The next complete utterance is treated as the command.
                        awaiting_command = False
                        self.command_ready.emit(text)
                        self.status_changed.emit("Command captured; listening for wake phrase again.")
                        continue

                    trailing = extract_command_after_wake_phrase(text, self.wake_phrase)
                    if trailing is None:
                        continue
                    if trailing:
                        self.command_ready.emit(trailing)
                        self.status_changed.emit("Command captured; listening for wake phrase again.")
                    else:
                        awaiting_command = True
                        self.status_changed.emit("Wake phrase detected. Say your command.")
        except Exception as exc:
            self.failed.emit(f"Offline voice listener stopped: {type(exc).__name__}: {exc}")
