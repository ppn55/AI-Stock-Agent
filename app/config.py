import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 獲取配置變數
GOOGLE_SHEET_URL = os.getenv(
    "GOOGLE_SHEET_URL",
    "https://docs.google.com/spreadsheets/d/1xICyi68ZtfgCSm5h5SBeBgz1oXLXID7cZK_v1i1a9h8/edit?gid=0#gid=0"
)

ZEABUR_API_KEY = os.getenv("ZEABUR_API_KEY", "")
ZEABUR_API_BASE = os.getenv("ZEABUR_API_BASE", "https://hnd1.aihub.zeabur.ai/v1")
ZEABUR_MODEL = os.getenv("ZEABUR_MODEL", "gpt-4o-mini")

RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
try:
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
except ValueError:
    SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def get_config_summary() -> dict:
    """回傳配置的摘要（隱藏 API 密鑰與密碼以策安全）"""
    return {
        "GOOGLE_SHEET_URL": GOOGLE_SHEET_URL,
        "ZEABUR_API_BASE": ZEABUR_API_BASE,
        "ZEABUR_MODEL": ZEABUR_MODEL,
        "ZEABUR_API_KEY_SET": bool(ZEABUR_API_KEY),
        "RECIPIENT_EMAIL": RECIPIENT_EMAIL,
        "SMTP_SERVER": SMTP_SERVER,
        "SMTP_PORT": SMTP_PORT,
        "SMTP_USER": SMTP_USER,
        "SMTP_PASSWORD_SET": bool(SMTP_PASSWORD)
    }


if __name__ == "__main__":
    print("=== Config Setup Check ===")
    for k, v in get_config_summary().items():
        print(f"{k}: {v}")
