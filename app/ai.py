import os
from typing import Dict, Any, List
from openai import OpenAI
from app import config


def format_holdings_detail(portfolio_metrics: Dict[str, Any], stock_indicators: Dict[str, Dict[str, Any]]) -> str:
    """
    將持股損益與技術指標格式化為 AI 容易理解的文字結構。
    """
    detail_lines = []
    
    for holding in portfolio_metrics["holdings"]:
        ticker = holding["ticker"]
        name = holding["name"]
        shares = holding["shares"]
        cost = holding["cost"]
        price = holding["price"]
        market_value = holding["market_value"]
        pnl = holding["unrealized_pnl"]
        return_rate = holding["return_rate"]
        ratio = holding["ratio"]
        
        ind = stock_indicators.get(ticker, {})
        
        ma20_val = ind.get("MA20")
        ma20_str = f"{ma20_val:.2f}" if ma20_val is not None else "無"
        
        ma60_val = ind.get("MA60")
        ma60_str = f"{ma60_val:.2f}" if ma60_val is not None else "無"
        
        rsi_val = ind.get("RSI")
        rsi_str = f"{rsi_val:.2f}" if rsi_val is not None else "無"
        
        macd_dif = ind.get("MACD_DIF")
        macd_dif_str = f"{macd_dif:.4f}" if macd_dif is not None else "無"
        
        macd_dea = ind.get("MACD_DEA")
        macd_dea_str = f"{macd_dea:.4f}" if macd_dea is not None else "無"
        
        macd_hist = ind.get("MACD_HIST")
        macd_hist_str = f"{macd_hist:.4f}" if macd_hist is not None else "無"
        
        k_val = ind.get("K")
        k_str = f"{k_val:.2f}" if k_val is not None else "無"
        
        d_val = ind.get("D")
        d_str = f"{d_val:.2f}" if d_val is not None else "無"
        
        bb_upper = ind.get("BB_UPPER")
        bb_upper_str = f"{bb_upper:.2f}" if bb_upper is not None else "無"
        
        bb_middle = ind.get("BB_MIDDLE")
        bb_middle_str = f"{bb_middle:.2f}" if bb_middle is not None else "無"
        
        bb_lower = ind.get("BB_LOWER")
        bb_lower_str = f"{bb_lower:.2f}" if bb_lower is not None else "無"
        
        vol_latest = ind.get("Vol_Latest")
        vol_latest_str = f"{vol_latest:,.0f} 張" if vol_latest is not None else "無"
        
        vol_ma5 = ind.get("Vol_MA5")
        vol_ma5_str = f"{vol_ma5:,.0f} 張" if vol_ma5 is not None else "無"
        
        vol_ma20 = ind.get("Vol_MA20")
        vol_ma20_str = f"{vol_ma20:,.0f} 張" if vol_ma20 is not None else "無"
        
        vol_ratio = ind.get("Vol_Ratio")
        vol_ratio_str = f"{vol_ratio:.2f} 倍" if vol_ratio is not None else "無"
        
        # 建立個股描述
        detail_lines.append(f"--- 股票: {ticker} ({name}) ---")
        detail_lines.append(f"  - 庫存明細: 持有 {shares:,} 股，買進總成本 {cost:,.0f} 元，目前股價 {price:.2f} 元，當前市值 {market_value:,.0f} 元")
        detail_lines.append(f"  - 目前損益: {pnl:,.0f} 元，報酬率 {return_rate:.2f}%，佔投資組合比例 {ratio:.2f}%")
        
        # 建立技術指標描述
        detail_lines.append("  - 技術指標:")
        detail_lines.append(f"    * 收盤價: {price:.2f}")
        detail_lines.append(f"    * MA20 (月線): {ma20_str}")
        detail_lines.append(f"    * MA60 (季線): {ma60_str}")
        detail_lines.append(f"    * RSI (14日): {rsi_str}")
        detail_lines.append(f"    * MACD DIF: {macd_dif_str}, DEA: {macd_dea_str}, 柱狀值: {macd_hist_str}")
        detail_lines.append(f"    * KD 指標: K={k_str}, D={d_str}")
        detail_lines.append(f"    * 布林通道: 上軌={bb_upper_str}, 中軌={bb_middle_str}, 下軌={bb_lower_str}")
        detail_lines.append(f"    * 成交量能: 今日成交量={vol_latest_str}, 5日均量={vol_ma5_str}, 20日均量={vol_ma20_str}, 量比={vol_ratio_str}")
        
        # 技術面狀態說明
        detail_lines.append("  - 系統技術面狀態說明:")
        for sig in ind.get("signals", []):
            detail_lines.append(f"    * {sig}")
        detail_lines.append("")
        
    return "\n".join(detail_lines)


def get_ai_analysis(portfolio_metrics: Dict[str, Any], stock_indicators: Dict[str, Dict[str, Any]], custom_prompt_path: str = None) -> str:
    """
    呼叫 Zeabur OpenAI API 進行股票庫存評估分析。
    """
    # 1. 讀取 Prompt 範本
    prompt_path = custom_prompt_path or os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "prompts",
        "stock_analysis.txt"
    )
    
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"找不到 Prompt 範本檔案: {prompt_path}")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_tmpl = f.read()
        
    # 2. 格式化數據
    holdings_detail = format_holdings_detail(portfolio_metrics, stock_indicators)
    
    prompt = prompt_tmpl.format(
        total_cost=portfolio_metrics["total_cost"],
        total_market_value=portfolio_metrics["total_market_value"],
        total_pnl=portfolio_metrics["total_pnl"],
        total_return_rate=portfolio_metrics["total_return_rate"],
        holdings_detail=holdings_detail
    )
    
    # 3. 檢查 API 金鑰
    if not config.ZEABUR_API_KEY:
        print("警告: 未設定 ZEABUR_API_KEY，將回傳模擬 AI 分析建議。")
        return get_mock_analysis(portfolio_metrics)
        
    # 4. 呼叫 OpenAI API (Zeabur AI Hub)
    try:
        print(f"正在連線 Zeabur OpenAI API ({config.ZEABUR_API_BASE})... 使用模型: {config.ZEABUR_MODEL}")
        client = OpenAI(
            api_key=config.ZEABUR_API_KEY,
            base_url=config.ZEABUR_API_BASE
        )
        
        response = client.chat.completions.create(
            model=config.ZEABUR_MODEL,
            messages=[
                {"role": "system", "content": "你是一位專業的台灣股市理財專家與證券分析師，善於以精確的技術分析與基本面數據提供資產調整建議。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        
        analysis_result = response.choices[0].message.content
        print("AI 分析報告生成成功。")
        return analysis_result
        
    except Exception as e:
        print(f"呼叫 Zeabur API 時發生錯誤: {e}")
        print("將降級回傳模擬的分析建議。")
        return get_mock_analysis(portfolio_metrics, error_msg=str(e))


def get_mock_analysis(portfolio_metrics: Dict[str, Any], error_msg: str = None) -> str:
    """回傳模擬的分析結果，供測試或 API 金鑰失效時使用"""
    err_section = f"\n> [!WARNING]\n> API 呼叫失敗，以下為系統模擬報告。錯誤訊息: {error_msg}\n" if error_msg else ""
    
    holdings_pstr = ""
    for h in portfolio_metrics["holdings"]:
        holdings_pstr += f"- **{h['ticker']} {h['name']}**: 持有 {h['shares']} 股，目前損益 {h['unrealized_pnl']:,.0f} 元 ({h['return_rate']:.2f}%)\n"

    return f"""# 投資組合 AI Agent 評估報告 (模擬版)
{err_section}
## 一、 投資組合配置與風險分析
- **多元化評估**：本投資組合共包含 {len(portfolio_metrics['holdings'])} 檔持股。整體持股分佈於不同電子與傳統板塊，但建議進一步平衡防守型與積極型標的比例。
- **整體曝險與報酬率**：總買進成本為 {portfolio_metrics['total_cost']:,.0f} 元，目前總市值為 {portfolio_metrics['total_market_value']:,.0f} 元，未實現損益為 {portfolio_metrics['total_pnl']:,.0f} 元，整體報酬率為 {portfolio_metrics['total_return_rate']:.2f}%。目前整體損益呈現{"獲利" if portfolio_metrics['total_pnl'] >= 0 else "虧損"}狀態。

## 二、 個股深度技術面評估
{holdings_pstr}
### 模擬分析細節：
1. **技術面解讀**：
   - 目前部分個股處於月線上方（短期偏多），但需注意大盤成交量變化。KD指標與RSI多在50附近中性區間。
   - 布林通道呈現收斂狀態，暗示近期可能面臨方向性突破。
2. **操作建議**：
   - 建議維持續抱，並在接近季線位置設定防守停損點。
   - 對於報酬率為負且跌破月線的弱勢股，建議分批減碼。

## 三、 投資組合調整與再平衡建議
- 建議保留 15-20% 的現金，以應對市場潛在的波動。
- 可考慮於台股回檔至關鍵支撐時，逢低加碼具有產業前景之龍頭股。
"""


if __name__ == "__main__":
    # 測試 AI 模組與模擬功能
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
    
    print("=== 測試 AI 報告 (未配置 API KEY，應輸出模擬報告) ===")
    report = get_ai_analysis(mock_portfolio, mock_indicators)
    print(report)
