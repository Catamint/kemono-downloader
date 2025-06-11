import re
import unicodedata
import platform

def sanitize_filename(title: str, max_length=150) -> str:
    """将任意字符串转换为安全的 Windows 文件名"""
    title = re.sub(r'[\\/:*?"<>|]', '_', title)
    title = ''.join(c for c in title if unicodedata.category(c)[0] != "C")  # 控制符
    title = ''.join(c for c in title if unicodedata.category(c) != "So")  # emoji
    title = title.rstrip(' .')
    return title[:max_length].rstrip(' .')


def rename_list(previews):
    total_files = len(previews)
    digits = 1 if total_files < 10 else (2 if total_files < 100 else 3)

    for i, preview in enumerate(previews):
        file_extension = preview["name"].split(".")[-1]
        new_name = f"{(i + 1):0{digits}d}.{file_extension}"
        preview["name"] = new_name

    return previews


def set_hidden_windows(path):
    if platform.system() == "Windows":
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_HIDDEN)
        except Exception as e:
            print(f"设置隐藏属性失败: {e}")