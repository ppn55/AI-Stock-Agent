import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_ma(df: pd.DataFrame) -> pd.DataFrame:
    """計算 MA20 與 MA60"""
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """計算 14 日 RSI (使用 Wilder's Smoothing/EMA 算法)"""
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    # 使用 exponential moving average (com = period - 1)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    
    # 避免除以 0
    rs = np.where(avg_loss == 0, np.nan, avg_gain / avg_loss)
    df['RSI'] = np.where(pd.isna(rs), 100.0, np.where(avg_loss == 0, 100.0, 100.0 - (100.0 / (1.0 + rs))))
    return df


def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
    """計算 MACD (12, 26, 9)"""
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_DIF'] = ema12 - ema26
    df['MACD_DEA'] = df['MACD_DIF'].ewm(span=9, adjust=False).mean()
    df['MACD_HIST'] = df['MACD_DIF'] - df['MACD_DEA']
    return df


def calculate_kd(df: pd.DataFrame) -> pd.DataFrame:
    """計算 KD 指標 (9, 3, 3)"""
    # 獲取 9 日內最高價與最低價
    low_9 = df['Low'].rolling(window=9).min()
    high_9 = df['High'].rolling(window=9).max()
    
    # 計算 RSV
    # 避免分母為 0
    denom = high_9 - low_9
    rsv = np.where(denom == 0, 50.0, (df['Close'] - low_9) / denom * 100)
    
    k_val = 50.0
    d_val = 50.0
    k_list = []
    d_list = []
    
    for val in rsv:
        if pd.isna(val):
            k_list.append(np.nan)
            d_list.append(np.nan)
        else:
            k_val = (2.0 / 3.0) * k_val + (1.0 / 3.0) * val
            d_val = (2.0 / 3.0) * d_val + (1.0 / 3.0) * k_val
            k_list.append(k_val)
            d_list.append(d_val)
            
    df['K'] = k_list
    df['D'] = d_list
    return df


def calculate_bollinger_bands(df: pd.DataFrame) -> pd.DataFrame:
    """計算布林通道 (20, 2)"""
    ma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    df['BB_MIDDLE'] = ma20
    df['BB_UPPER'] = ma20 + 2 * std20
    df['BB_LOWER'] = ma20 - 2 * std20
    return df


def analyze_stock_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    計算股票的所有技術指標，並回傳最新的指標值與狀態描述。
    """
    # 複製 DataFrame 避免污染原始數據
    df_calc = df.copy()
    
    # 依序計算指標
    df_calc = calculate_ma(df_calc)
    df_calc = calculate_rsi(df_calc)
    df_calc = calculate_macd(df_calc)
    df_calc = calculate_kd(df_calc)
    df_calc = calculate_bollinger_bands(df_calc)
    
    # 計算成交量指標 (yfinance 為原始股數，除以 1000 轉換為台灣市場慣用的「張」)
    df_calc['Vol_Latest'] = df_calc['Volume'] / 1000.0
    df_calc['Vol_MA5'] = df_calc['Volume'].rolling(window=5).mean() / 1000.0
    df_calc['Vol_MA20'] = df_calc['Volume'].rolling(window=20).mean() / 1000.0
    df_calc['Vol_Ratio'] = df_calc['Vol_Latest'] / df_calc['Vol_MA20']
    
    # 獲取最新一筆的數據
    latest = df_calc.iloc[-1]
    
    # 建立指標狀態報告
    indicators = {
        "Close": float(latest["Close"]),
        "MA20": float(latest["MA20"]) if not pd.isna(latest["MA20"]) else None,
        "MA60": float(latest["MA60"]) if not pd.isna(latest["MA60"]) else None,
        "RSI": float(latest["RSI"]) if not pd.isna(latest["RSI"]) else None,
        "MACD_DIF": float(latest["MACD_DIF"]) if not pd.isna(latest["MACD_DIF"]) else None,
        "MACD_DEA": float(latest["MACD_DEA"]) if not pd.isna(latest["MACD_DEA"]) else None,
        "MACD_HIST": float(latest["MACD_HIST"]) if not pd.isna(latest["MACD_HIST"]) else None,
        "K": float(latest["K"]) if not pd.isna(latest["K"]) else None,
        "D": float(latest["D"]) if not pd.isna(latest["D"]) else None,
        "BB_MIDDLE": float(latest["BB_MIDDLE"]) if not pd.isna(latest["BB_MIDDLE"]) else None,
        "BB_UPPER": float(latest["BB_UPPER"]) if not pd.isna(latest["BB_UPPER"]) else None,
        "BB_LOWER": float(latest["BB_LOWER"]) if not pd.isna(latest["BB_LOWER"]) else None,
        "Vol_Latest": float(latest["Vol_Latest"]),
        "Vol_MA5": float(latest["Vol_MA5"]) if not pd.isna(latest["Vol_MA5"]) else None,
        "Vol_MA20": float(latest["Vol_MA20"]) if not pd.isna(latest["Vol_MA20"]) else None,
        "Vol_Ratio": float(latest["Vol_Ratio"]) if not pd.isna(latest["Vol_Ratio"]) else None,
    }
    
    # 生成簡單的技術面狀態說明
    tech_signals = []
    close = indicators["Close"]
    
    # MA 關係
    if indicators["MA20"] and indicators["MA60"]:
        if close > indicators["MA20"]:
            tech_signals.append("股價在月線 (MA20) 之上，短期呈偏多趨勢。")
        else:
            tech_signals.append("股價在月線 (MA20) 之下，短期呈偏空整理。")
            
        if indicators["MA20"] > indicators["MA60"]:
            tech_signals.append("月線大於季線，均線呈現多頭排列。")
        else:
            tech_signals.append("月線小於季線，均線呈現空頭排列。")
            
    # RSI 關係
    if indicators["RSI"]:
        rsi = indicators["RSI"]
        if rsi >= 70:
            tech_signals.append(f"RSI 為 {rsi:.1f}，進入超買區，需留意回檔風險。")
        elif rsi <= 30:
            tech_signals.append(f"RSI 為 {rsi:.1f}，進入超賣區，可留意反彈契機。")
        else:
            tech_signals.append(f"RSI 為 {rsi:.1f}，處於中性區間。")
            
    # KD 關係
    if indicators["K"] and indicators["D"]:
        k, d = indicators["K"], indicators["D"]
        if k > d:
            tech_signals.append(f"KD 指標黃金交叉 (K={k:.1f}, D={d:.1f})，走勢偏強。")
        else:
            tech_signals.append(f"KD 指標死亡交叉 (K={k:.1f}, D={d:.1f})，走勢偏弱。")
            
    # 布林通道關係
    if indicators["BB_UPPER"] and indicators["BB_LOWER"]:
        upper, lower = indicators["BB_UPPER"], indicators["BB_LOWER"]
        if close >= upper:
            tech_signals.append("股價突破布林通道上軌，強勢噴發或面臨過熱。")
        elif close <= lower:
            tech_signals.append("股價跌破布林通道下軌，極度弱勢或存在超跌。")
        else:
            tech_signals.append("股價在布林通道內部震盪整理。")
            
    # 成交量關係
    if indicators["Vol_Ratio"]:
        ratio = indicators["Vol_Ratio"]
        vol_latest = indicators["Vol_Latest"]
        if ratio >= 2.0:
            tech_signals.append(f"成交量顯著爆量 ({vol_latest:,.0f}張，量比達 {ratio:.1f}倍)，短線動能強勁！")
        elif ratio >= 1.5:
            tech_signals.append(f"成交量明顯增量 ({vol_latest:,.0f}張，量比達 {ratio:.1f}倍)，短線有資金流入跡象。")
        elif ratio <= 0.5:
            tech_signals.append(f"成交量明顯萎縮 ({vol_latest:,.0f}張，量比僅 {ratio:.1f}倍)，呈現無量盤整。")
        else:
            tech_signals.append(f"成交量處於常態水準 ({vol_latest:,.0f}張，量比 {ratio:.1f}倍)。")
            
    indicators["signals"] = tech_signals
    return indicators


def process_portfolio_metrics(holdings_df: pd.DataFrame, latest_prices: Dict[str, float]) -> Dict[str, Any]:
    """
    根據持股資訊與最新價格計算未實現損益、佔比等投資組合數據。
    
    holdings_df 的欄位：股票代號, 股票名稱, 股數, 成本
    """
    portfolio = []
    total_cost = 0.0
    total_market_value = 0.0
    
    # 1. 整理持股並計算損益
    for _, row in holdings_df.iterrows():
        ticker = row["股票代號"]
        name = row["股票名稱"]
        
        # 轉換股數與成本為數值，移除可能存在的千分位逗號
        shares = int(str(row["股數"]).replace(",", ""))
        
        # 成本可能是單股成本或是總成本，試算表中 47,490 應該是「總成本」（台泥 2000股，現價約30~40元，總成本47,490元是合理的）
        # 我們將在此統一將「成本」當作「買進總成本」處理。
        cost_str = str(row["成本"]).replace(",", "").replace("$", "")
        cost = float(cost_str)
        
        current_price = latest_prices.get(ticker, 0.0)
        market_value = current_price * shares
        unrealized_pnl = market_value - cost
        return_rate = (unrealized_pnl / cost * 100) if cost > 0 else 0.0
        
        total_cost += cost
        total_market_value += market_value
        
        portfolio.append({
            "ticker": ticker,
            "name": name,
            "shares": shares,
            "cost": cost,
            "price": current_price,
            "market_value": market_value,
            "unrealized_pnl": unrealized_pnl,
            "return_rate": return_rate
        })
        
    # 2. 計算投資組合比例佔比
    for item in portfolio:
        item["ratio"] = (item["market_value"] / total_market_value * 100) if total_market_value > 0 else 0.0
        
    total_pnl = total_market_value - total_cost
    total_return_rate = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0
    
    return {
        "holdings": portfolio,
        "total_cost": total_cost,
        "total_market_value": total_market_value,
        "total_pnl": total_pnl,
        "total_return_rate": total_return_rate
    }


if __name__ == "__main__":
    from app.market import download_stock_data
    test_tickers = ["1101.TW", "2330.TW"]
    print("下載測試資料中...")
    k_data = download_stock_data(test_tickers)
    
    for ticker, df in k_data.items():
        print(f"\n=== {ticker} 技術指標計算結果 ===")
        indicators = analyze_stock_indicators(df)
        for k, v in indicators.items():
            if k != "signals":
                print(f"  {k}: {v}")
        print("  技術面狀態:")
        for sig in indicators["signals"]:
            print(f"    - {sig}")

