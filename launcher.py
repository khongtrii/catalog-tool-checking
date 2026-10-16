from __future__ import annotations

import os
from pathlib import Path
import socket
import sys
import threading
import time
import traceback
import webbrowser

from streamlit.web import bootstrap


HOST = "127.0.0.1"
FIRST_PORT = 8501
LAST_PORT = 8599


def find_available_port(start: int = FIRST_PORT, end: int = LAST_PORT) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            try:
                candidate.bind((HOST, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"Không còn cổng trống trong khoảng {start}-{end}.")


def resource_root() -> Path:
    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        return Path(bundled_root)
    return Path(__file__).resolve().parent


def open_browser_when_ready(port: int, timeout_seconds: float = 30.0) -> None:
    url = f"http://{HOST}:{port}"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((HOST, port), timeout=0.25):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(0.2)
    print(f"Không thể tự mở trình duyệt. Hãy truy cập: {url}")


def streamlit_options(port: int) -> dict[str, object]:
    return {
        "global.developmentMode": False,
        "server.address": HOST,
        "server.port": port,
        "server.headless": True,
        "server.fileWatcherType": "none",
        "browser.gatherUsageStats": False,
    }


def run() -> None:
    root = resource_root()
    app_path = root / "app.py"
    if not app_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy ứng dụng tại: {app_path}")

    os.chdir(root)
    port = find_available_port()
    url = f"http://{HOST}:{port}"
    print("Catalog Price Checker đang khởi động...")
    print(f"Địa chỉ local: {url}")
    print("Đóng cửa sổ này để dừng ứng dụng.")

    if os.environ.get("CATALOG_CHECKER_NO_BROWSER") != "1":
        browser_thread = threading.Thread(
            target=open_browser_when_ready,
            args=(port,),
            name="browser-opener",
            daemon=True,
        )
        browser_thread.start()

    options = streamlit_options(port)
    # The Streamlit CLI normally performs this initial config load. A packaged
    # launcher calls bootstrap directly, so it must apply the flags explicitly.
    bootstrap.load_config_options(options)
    bootstrap.run(
        str(app_path),
        False,
        [],
        options,
    )


def main() -> int:
    try:
        run()
    except KeyboardInterrupt:
        print("\nĐang dừng Catalog Price Checker...")
        return 0
    except Exception:
        print("Không thể khởi động Catalog Price Checker.")
        traceback.print_exc()
        try:
            input("Nhấn Enter để đóng cửa sổ...")
        except EOFError:
            pass
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
