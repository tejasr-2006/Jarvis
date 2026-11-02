"""Optional Qt desktop shell for JARVIS.

Install optional desktop dependencies from requirements-desktop.txt, then run
`python -m app.desktop` from the project root. The API key is kept in memory
for this process only. This module does not enable microphone listening.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QSystemTrayIcon,
    QMenu,
    QStyle,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOST = os.getenv("JARVIS_DESKTOP_HOST", "127.0.0.1")
PORT = int(os.getenv("JARVIS_DESKTOP_PORT", "8000"))
BASE_URL = f"http://{HOST}:{PORT}"


def _get_json(path: str, api_key: str = "", timeout: float = 2.0):
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-JARVIS-API-Key"] = api_key
    request = urllib.request.Request(BASE_URL + path, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(path: str, api_key: str = "", timeout: float = 2.0):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if api_key:
        headers["X-JARVIS-API-Key"] = api_key
    request = urllib.request.Request(BASE_URL + path, data=b"{}", headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _backend_responds() -> bool:
    try:
        data = _get_json("/health", timeout=1.0)
        return data.get("status") == "healthy"
    except Exception:
        return False


def _wait_for_backend(process: Optional[subprocess.Popen], timeout: float = 25.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _backend_responds():
            return True
        if process is not None and process.poll() is not None:
            return False
        time.sleep(0.25)
    return False


class JarvisDesktop(QMainWindow):
    def __init__(self, backend_process: Optional[subprocess.Popen] = None):
        super().__init__()
        self.backend_process = backend_process
        self.api_key = ""
        self.notified_ids: set[int] = set()
        self.setWindowTitle("JARVIS — Personal AI Assistant")
        self.resize(1280, 850)

        self.web = QWebEngineView(self)
        self.web.setUrl(QUrl(BASE_URL + "/dashboard"))
        self.setCentralWidget(self.web)

        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self)
            self.tray.setToolTip("JARVIS")
            self.tray.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
            menu = QMenu()
            show_action = QAction("Open JARVIS", self)
            show_action.triggered.connect(self.showNormal)
            menu.addAction(show_action)
            key_action = QAction("Set notification API key", self)
            key_action.triggered.connect(self.set_api_key)
            menu.addAction(key_action)
            wake_action = QAction("Enable offline wake listening", self)
            wake_action.triggered.connect(self.enable_wake_listening)
            menu.addAction(wake_action)
            stop_wake_action = QAction("Stop wake listening", self)
            stop_wake_action.triggered.connect(self.stop_wake_listening)
            menu.addAction(stop_wake_action)
            exit_action = QAction("Exit JARVIS", self)
            exit_action.triggered.connect(self.close)
            menu.addAction(exit_action)
            self.tray.setContextMenu(menu)
            self.tray.show()

        self.notification_timer = QTimer(self)
        self.notification_timer.setInterval(30_000)
        self.notification_timer.timeout.connect(self.poll_notifications)
        self.notification_timer.start()

        QTimer.singleShot(500, self.set_api_key)

    def set_api_key(self):
        value, accepted = QInputDialog.getText(
            self,
            "JARVIS notifications",
            "Optional: enter your JARVIS API key to enable desktop reminder notifications.\n"
            "It stays in memory only and is not saved to disk.",
            QInputDialog.EchoMode.Password,
        )
        if accepted and value.strip():
            self.api_key = value.strip()
            self.poll_notifications()

    def enable_wake_listening(self):
        if self.wake_listener is not None and self.wake_listener.isRunning():
            if self.tray:
                self.tray.showMessage("JARVIS", "Offline wake listening is already enabled.")
            return

        if not self.api_key:
            value, accepted = QInputDialog.getText(
                self,
                "JARVIS API key",
                "Enter your JARVIS API key to submit voice commands. It stays in memory only.",
                QInputDialog.EchoMode.Password,
            )
            if not accepted or not value.strip():
                return
            self.api_key = value.strip()

        model_path = os.getenv("JARVIS_VOSK_MODEL_PATH", "").strip()
        if not model_path or not os.path.isdir(model_path):
            model_path = QFileDialog.getExistingDirectory(
                self,
                "Select extracted Vosk model folder",
                str(Path.home()),
            )
        if not model_path:
            if self.tray:
                self.tray.showMessage("JARVIS", "Wake listening cancelled; no model selected.")
            return

        wake_phrase = os.getenv("JARVIS_WAKE_PHRASE", "jarvis").strip() or "jarvis"
        try:
            from app.voice.listener import WakeWordListener
            self.wake_listener = WakeWordListener(model_path, wake_phrase, self)
            self.wake_listener.command_ready.connect(self.submit_voice_command)
            self.wake_listener.status_changed.connect(self.voice_status)
            self.wake_listener.failed.connect(self.voice_failed)
            self.wake_listener.start()
            if self.tray:
                self.tray.showMessage(
                    "JARVIS",
                    "Offline wake listening is starting. Say the configured wake phrase.",
                )
        except Exception as exc:
            QMessageBox.warning(self, "Voice setup failed", f"{type(exc).__name__}: {exc}")

    def stop_wake_listening(self):
        listener = self.wake_listener
        self.wake_listener = None
        if listener is not None:
            try:
                if listener.isRunning():
                    listener.stop()
                listener.deleteLater()
            except Exception:
                pass
        if self.tray:
            self.tray.showMessage("JARVIS", "Wake listening stopped.")

    def voice_status(self, message: str):
        if self.tray:
            self.tray.setToolTip(("JARVIS — " + message)[:120])

    def voice_failed(self, message: str):
        if self.tray:
            self.tray.showMessage("JARVIS voice", message[:240])
        else:
            QMessageBox.warning(self, "JARVIS voice", message)

    def submit_voice_command(self, command: str):
        command = command.strip()
        if not command:
            return
        if not self.api_key:
            self.voice_failed("No API key is set; voice command was not submitted.")
            return
        try:
            payload = json.dumps({"command": command}).encode("utf-8")
            request = urllib.request.Request(
                BASE_URL + "/command",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-JARVIS-API-Key": self.api_key,
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=35.0) as response:
                data = json.loads(response.read().decode("utf-8"))
            result = data.get("result", {})
            status = result.get("status", "completed") if isinstance(result, dict) else "completed"
            message = f"Heard: {command[:100]} | Result: {status}"
            if self.tray:
                self.tray.showMessage("JARVIS voice command", message[:240])
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:180]
            self.voice_failed(f"Voice command rejected (HTTP {exc.code}): {detail}")
        except Exception as exc:
            self.voice_failed(f"Voice command failed: {type(exc).__name__}")

    def poll_notifications(self):
        if not self.api_key or not self.tray:
            return
        try:
            data = _get_json("/notifications?limit=50", api_key=self.api_key, timeout=3.0)
            for item in data.get("notifications", []):
                reminder_id = int(item.get("id", 0))
                if not reminder_id or reminder_id in self.notified_ids:
                    continue
                self.notified_ids.add(reminder_id)
                title = str(item.get("title", "JARVIS notification"))[:120]
                message = str(item.get("message", ""))[:240]
                kind = str(item.get("kind", "reminder"))
                heading = "JARVIS alert" if kind.startswith("task_") else "JARVIS reminder"
                self.tray.showMessage(heading, title + ("\n" + message if message else ""), QSystemTrayIcon.MessageIcon.Information, 10_000)
                # Mark displayed items as acknowledged so they do not reappear after restart.
                try:
                    _post_json(f"/notifications/{reminder_id}/ack", api_key=self.api_key, timeout=3.0)
                except Exception:
                    pass
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                self.api_key = ""
        except Exception:
            # The dashboard remains available even if notifications are temporarily offline.
            pass

    def closeEvent(self, event: QCloseEvent):
        self.stop_wake_listening()
        if self.tray:
            self.tray.hide()
        if self.backend_process is not None and self.backend_process.poll() is None:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
        self.api_key = ""
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    backend_process = None

    if not _backend_responds():
        try:
            backend_process = subprocess.Popen(
                [
                    sys.executable, "-m", "uvicorn", "app.main:app",
                    "--host", HOST, "--port", str(PORT),
                ],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            QMessageBox.critical(None, "JARVIS startup failed", f"Could not start backend:\n{exc}")
            return 1

    if not _wait_for_backend(backend_process):
        if backend_process and backend_process.poll() is None:
            backend_process.terminate()
        QMessageBox.critical(
            None,
            "JARVIS startup failed",
            f"JARVIS API did not become healthy at {BASE_URL}.\n"
            "Check your .env file and whether the port is already in use.",
        )
        return 1

    window = JarvisDesktop(backend_process)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
