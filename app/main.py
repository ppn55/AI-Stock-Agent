import sys
import os
from datetime import datetime
from app import config
from app.holdings import get_holdings
from app.market import download_stock_data, get_latest_prices
from app.indicators import analyze_stock_indicators, process_portfolio_metrics
from app.ai import get_ai_analysis
from app.report import generate_html_report
from app.mail import send_email_report


def run_daily_analysis() -> bool:
    """
    執行每日股票庫存分析與建議生成的完整工作流。
    """
    print(f"\n==========================================")
    print(f"  AI Stock Agent 每日分析啟動: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"==========================================\n")
    
    try:
        # 1. 讀取 Google 試算表庫存資料
        print("[Step 1] 正在讀取庫存資料...")
        sheet_url = config.GOOGLE_SHEET_URL
        print(f"試算表網址: {sheet_url}")
        holdings_df = get_holdings(sheet_url)
        
        # 檢查資料是否有必要欄位
        required_cols = ["股票代號", "股票名稱", "股數", "成本"]
        for col in required_cols:
            if col not in holdings_df.columns:
                # 試算表欄位名稱可能因為多餘空白字元造成不匹配，進行模糊匹配
                matching_cols = [c for c in holdings_df.columns if col in c]
                if matching_cols:
                    holdings_df.rename(columns={matching_cols[0]: col}, inplace=True)
                else:
                    raise ValueError(f"試算表缺少必要欄位 '{col}'。現有欄位: {list(holdings_df.columns)}")
        
        # 過濾空行與清理代號（台灣股市代號例如 2330.TW 或 0050.TW）
        holdings_df = holdings_df.dropna(subset=["股票代號"])
        holdings_df["股票代號"] = holdings_df["股票代號"].astype(str).str.strip()
        tickers = holdings_df["股票代號"].tolist()
        
        print(f"成功加載庫存持股，共 {len(tickers)} 檔標的: {tickers}")
        
        # 2. 下載個股市場行情數據
        print("\n[Step 2] 正在下載市場行情與 200 天 K 線...")
        k_data = download_stock_data(tickers)
        latest_prices = get_latest_prices(tickers, downloaded_data=k_data)
        
        # 3. 計算技術指標與投資組合分析
        print("\n[Step 3] 正在計算技術分析指標與投資組合損益...")
        stock_indicators = {}
        for ticker in tickers:
            if ticker in k_data:
                # 計算該股技術指標
                indicators = analyze_stock_indicators(k_data[ticker])
                stock_indicators[ticker] = indicators
            else:
                print(f"警告: 無法為 {ticker} 計算技術指標（缺乏歷史 K 線數據）。")
                stock_indicators[ticker] = {"Close": latest_prices.get(ticker, 0.0), "signals": ["無法獲取 K 線數據"]}
                
        portfolio_metrics = process_portfolio_metrics(holdings_df, latest_prices)
        
        # 4. 呼叫 Zeabur AI Hub 進行 AI 評估分析
        print("\n[Step 4] 正在呼叫 AI Agent 進行評估建議...")
        ai_analysis_md = get_ai_analysis(portfolio_metrics, stock_indicators)
        
        # 5. 產生 HTML 報告
        print("\n[Step 5] 正在生成 HTML 報告檔案...")
        html_content, report_path = generate_html_report(portfolio_metrics, stock_indicators, ai_analysis_md)
        
        # 6. 發送電子郵件通知
        print("\n[Step 6] 正在發送電子郵件...")
        email_sent = send_email_report(html_content)
        
        print("\n==========================================")
        print(f"  AI Stock Agent 分析執行完成！")
        print(f"  報告位置: {report_path}")
        print(f"  郵件狀態: {'成功發送' if email_sent else '未發送 / 發送失敗'}")
        print(f"==========================================\n")
        return True
        
    except Exception as e:
        print(f"\n[錯誤] 執行每日分析工作流時發生異常:")
        import traceback
        traceback.print_exc()
        print("==========================================\n")
        return False


if __name__ == "__main__":
    success = run_daily_analysis()
    sys.exit(0 if success else 1)
