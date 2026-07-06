import os
from datetime import datetime
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
import markdown


def generate_html_report(
    portfolio_metrics: Dict[str, Any],
    stock_indicators: Dict[str, Dict[str, Any]],
    ai_analysis_md: str
) -> tuple[str, str]:
    """
    結合持股、技術指標及 AI 建議，渲染並儲存一個精美的 HTML 報告。
    
    Returns:
        tuple[str, str]: (渲染後的 HTML 內容, 儲存的檔案路徑)
    """
    # 1. 確保 reports 資料夾存在
    base_dir = os.path.dirname(os.path.dirname(__file__))
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # 2. 初始化 Jinja2 環境
    templates_dir = os.path.join(base_dir, "templates")
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("email.html")
    
    # 3. 處理 AI 分析 markdown 為 HTML 並清理 .TW / .TWO 後綴避免被郵件軟體自動轉換成超連結
    import re
    cleaned_ai_md = re.sub(r'\b(\w+)\.TW\b', r'\1 TW', ai_analysis_md, flags=re.IGNORECASE)
    cleaned_ai_md = re.sub(r'\b(\w+)\.TWO\b', r'\1 TWO', cleaned_ai_md, flags=re.IGNORECASE)
    
    # 支援額外的 markdown 擴充功能（如表格、警告方塊等）
    ai_analysis_html = markdown.markdown(
        cleaned_ai_md,
        extensions=["extra", "admonition", "nl2br"]
    )
    
    # 4. 準備渲染所需的變數
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    total_cost_num = portfolio_metrics["total_cost"]
    total_mv_num = portfolio_metrics["total_market_value"]
    total_pnl_num = portfolio_metrics["total_pnl"]
    total_rr_num = portfolio_metrics["total_return_rate"]
    
    render_vars = {
        "report_date": now_str,
        "holdings": portfolio_metrics["holdings"],
        "indicators": stock_indicators,
        "total_cost": f"{total_cost_num:,.0f}",
        "total_market_value": f"{total_mv_num:,.0f}",
        "total_pnl": f"{total_pnl_num:+,.0f}",
        "total_return_rate": f"{total_rr_num:+.2f}%",
        "total_pnl_num": total_pnl_num,
        "total_return_rate_num": total_rr_num,
        "ai_analysis_html": ai_analysis_html
    }
    
    # 5. 渲染模板
    html_content = template.render(render_vars)
    
    # 6. 儲存至本地檔案
    file_date = datetime.now().strftime("%Y%m%d")
    report_file = os.path.join(reports_dir, f"report_{file_date}.html")
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"HTML 報告成功儲存至: {report_file}")
    
    return html_content, report_file


if __name__ == "__main__":
    # 測試報告生成
    mock_portfolio = {
        "holdings": [
            {
                "ticker": "1101.TW",
                "name": "台泥",
                "shares": 2000,
                "cost": 47490.0,
                "price": 23.70,
                "market_value": 47400.0,
                "unrealized_pnl": -90.0,
                "return_rate": -0.19,
                "ratio": 1.89
            },
            {
                "ticker": "2330.TW",
                "name": "台積電",
                "shares": 1000,
                "cost": 1000000.0,
                "price": 2460.0,
                "market_value": 2460000.0,
                "unrealized_pnl": 1460000.0,
                "return_rate": 146.00,
                "ratio": 98.11
            }
        ],
        "total_cost": 1047490.0,
        "total_market_value": 2507400.0,
        "total_pnl": 1459910.0,
        "total_return_rate": 139.37
    }
    
    mock_indicators = {
        "1101.TW": {
            "Close": 23.70,
            "MA20": 23.45,
            "MA60": 23.66,
            "RSI": 53.88,
            "MACD_DIF": -0.037,
            "MACD_DEA": -0.047,
            "MACD_HIST": 0.01,
            "K": 36.08,
            "D": 25.97,
            "BB_MIDDLE": 23.45,
            "BB_UPPER": 24.03,
            "BB_LOWER": 22.88,
            "signals": ["股價在月線 (MA20) 之上，短期呈偏多趨勢。", "月線小於季線，均線呈現空頭排列。"]
        },
        "2330.TW": {
            "Close": 2460.0,
            "MA20": 2387.09,
            "MA60": 2268.43,
            "RSI": 58.32,
            "MACD_DIF": 45.85,
            "MACD_DEA": 45.58,
            "MACD_HIST": 0.27,
            "K": 63.64,
            "D": 57.88,
            "BB_MIDDLE": 2387.09,
            "BB_UPPER": 2545.68,
            "BB_LOWER": 2228.50,
            "signals": ["股價在月線 (MA20) 之上，短期呈偏多趨勢。", "月線大於季線，均線呈現多頭排列。"]
        }
    }
    
    mock_ai_md = """# 投資組合 AI Agent 評估報告
    
## 一、 投資組合配置與風險分析
- **多元化評估**：本投資組合高度集中在 **台積電** (98.11%)，面臨極高的個股集中風險。
- **整體損益狀況**：目前總成本為 1,047,490 元，市值 2,507,400 元，大幅獲利 +1,459,910 元。

## 二、 個股深度技術面評估
1. **台泥 (1101.TW)**：
   - 目前略低於成本價，報酬率為 -0.19%。
   - 技術面上雖然股價在月線上，但月線小於季線呈空頭排列，指標處於中性偏弱狀態。
   - **操作建議**：續抱持有。
2. **台積電 (2330.TW)**：
   - 表現極度強勢，報酬率達 +146%。
   - 技術指標顯示多頭趨勢不變，KD 呈黃金交叉，股價在均線之上。
   - **操作建議**：分批獲利了結或設定移動停利點。
"""

    print("=== 測試 HTML 報告生成 ===")
    html, path = generate_html_report(mock_portfolio, mock_indicators, mock_ai_md)
    print("報告檔案路徑:", path)
