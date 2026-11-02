"""Allow-listed desktop actions. Never executes arbitrary shell commands."""
import platform
import subprocess
import webbrowser
from urllib.parse import urlsplit

ALLOWED_APPS = {
    "notepad": "Simple text editor",
    "calculator": "Calculator",
    "files": "File manager",
}

def validate_action(action_type: str, target: str) -> tuple[str, str]:
    action_type = action_type.strip().lower()
    target = target.strip()
    if action_type == "open_url":
        parsed = urlsplit(target)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Only complete http:// or https:// URLs are allowed.")
        if parsed.username or parsed.password:
            raise ValueError("URLs containing embedded credentials are not allowed.")
        if len(target) > 2048:
            raise ValueError("URL is too long.")
        return action_type, target
    if action_type == "launch_app":
        app = target.lower()
        if app not in ALLOWED_APPS:
            raise ValueError(f"Unsupported app. Choose one of: {', '.join(ALLOWED_APPS)}.")
        return action_type, app
    raise ValueError("Unsupported action type. Use open_url or launch_app.")

def execute_action(action_type: str, target: str) -> dict:
    """Execute only a previously validated and explicitly confirmed action."""
    action_type, target = validate_action(action_type, target)
    if action_type == "open_url":
        opened = webbrowser.open(target, new=2)
        if not opened:
            # webbrowser may return False even if a platform handler was invoked.
            # Report honestly rather than claiming verified success.
            return {"message": "Browser open request was issued; verify the browser window.", "verified": False}
        return {"message": "Browser open request issued.", "verified": True}

    system = platform.system()
    if target == "notepad":
        commands = {
            "Windows": ["notepad.exe"],
            "Darwin": ["open", "-a", "TextEdit"],
            "Linux": ["gedit"],
        }
    elif target == "calculator":
        commands = {
            "Windows": ["calc.exe"],
            "Darwin": ["open", "-a", "Calculator"],
            "Linux": ["gnome-calculator"],
        }
    else:  # files
        commands = {
            "Windows": ["explorer.exe"],
            "Darwin": ["open", "."],
            "Linux": ["xdg-open", "."],
        }
    command = commands.get(system)
    if not command:
        raise RuntimeError(f"Unsupported operating system: {system}")
    try:
        subprocess.Popen(command, shell=False, close_fds=(system != "Windows"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"The configured application is not available on {system}.") from exc
    return {"message": f"Launch request issued for {target}.", "verified": False}
