import re
from urllib.parse import parse_qs, urlparse

import pandas as pd


def _build_csv_export_url(sheet_url: str) -> str:
    if "/export?format=csv" in sheet_url:
        return sheet_url

    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", sheet_url)
    if not match:
        raise ValueError("無法從試算表連結擷取 sheet ID，請確認 URL 是否正確。")

    sheet_id = match.group(1)
    parsed = urlparse(sheet_url)
    query = parse_qs(parsed.query)
    gid = query.get("gid", [None])[0]
    if gid is None and parsed.fragment:
        fragment_query = parse_qs(parsed.fragment)
        gid = fragment_query.get("gid", [None])[0]
    if gid is None:
        gid = "0"

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def get_holdings(sheet_url: str) -> pd.DataFrame:
    csv_url = _build_csv_export_url(sheet_url)
    print(csv_url)
    df = pd.read_csv(csv_url)

    if df.shape[1] == 1:
        first_value = str(df.iat[0, 0]).strip().lower()
        if first_value.startswith("<!doctype") or first_value.startswith("<html"):
            raise RuntimeError(
                "讀取到 HTML 而非 CSV。請確認 Google 試算表分享設定為「任何取得連結的人都可查看」，"
                "並使用正確的試算表連結。"
            )

    return df


if __name__ == "__main__":
    sheet_url = "https://docs.google.com/spreadsheets/d/1xICyi68ZtfgCSm5h5SBeBgz1oXLXID7cZK_v1i1a9h8/edit?gid=0#gid=0"

    try:
        df = get_holdings(sheet_url)
        print("\n=== Holdings Data ===\n")
        print(df)
    except Exception as exc:
        print("Error:", exc)
