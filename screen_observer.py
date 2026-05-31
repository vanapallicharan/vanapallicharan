import datetime
import json
from pathlib import Path

from morpho_core.config import Config
from morpho_core.permission_manager import permission_manager

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import pytesseract
except Exception:
    pytesseract = None


class ScreenObserver:
    def __init__(self):
        dirs = Config.ensure_storage_dirs()
        self.enabled = Config.SCREEN_OBSERVER_DEFAULT
        self.screens_dir = Path(dirs["screens"])
        self.logs_path = Path(dirs["logs"]) / "screen_observer.jsonl"
        self.state_path = Path(dirs["state"]) / "screen_observer.json"

    def set_enabled(self, enabled: bool) -> dict:
        self.enabled = bool(enabled)
        self.state_path.write_text(json.dumps({"enabled": self.enabled}, indent=2), encoding="utf-8")
        permission_manager.log_action("screen_observer.toggle", {"enabled": self.enabled}, status="updated")
        return {"enabled": self.enabled}

    def capture_snapshot(self) -> dict:
        if not self.enabled:
            return {"enabled": False, "message": "screen observer is disabled"}
        if pyautogui is None:
            return {"enabled": True, "error": "pyautogui is unavailable"}

        timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
        screenshot_path = self.screens_dir / f"screen_{timestamp}.png"
        image = pyautogui.screenshot()
        image.save(screenshot_path)

        visible_text = ""
        if Config.OCR_ENABLED and pytesseract is not None:
            try:
                visible_text = pytesseract.image_to_string(image).strip()
            except Exception:
                visible_text = ""

        result = {
            "enabled": True,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "path": str(screenshot_path),
            "visible_text": visible_text[:4000],
            "app_context": visible_text.splitlines()[:5],
        }
        with self.logs_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")
        permission_manager.log_action("screen_observer.capture", {"path": str(screenshot_path)}, status="captured")
        return result


screen_observer = ScreenObserver()
