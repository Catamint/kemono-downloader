import os
import sys
import platform
import json

def get_app_meta_dir():
    """
    自动检测并返回一个适用于 Windows/Android/Linux/macOS 的元数据目录
    保证可写，无需用户干预。
    """
    app_name = "KemonoDownloader"
    meta_dir_name = "meta"

    # Android 判断：环境变量或 platform
    if "ANDROID_STORAGE" in os.environ or "ANDROID_ROOT" in os.environ:
        home = os.environ.get("HOME") or "/data/data/com.termux/files/home"
        meta_path = os.path.join(home, app_name, meta_dir_name)
    elif platform.system() == "Linux" and "android" in platform.platform().lower():
        home = os.environ.get("HOME") or "/data/data/com.termux/files/home"
        meta_path = os.path.join(home, app_name, meta_dir_name)
    # Windows
    elif platform.system() == "Windows":
        local_app = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
        meta_path = os.path.join(local_app, app_name, meta_dir_name)
    # macOS/Linux 桌面
    else:
        home = os.path.expanduser("~")
        meta_path = os.path.join(home, ".config", app_name, meta_dir_name)

    os.makedirs(meta_path, exist_ok=True)
    return meta_path

def get_status_path(user_id: str):
    return os.path.join(get_app_meta_dir(), f"{user_id}_download_status.json")

def load_status(user_id: str):
    status_path = get_status_path(user_id)
    if os.path.exists(status_path):
        with open(status_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def save_status(user_id: str, status: dict):
    status_path = get_status_path(user_id)
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
