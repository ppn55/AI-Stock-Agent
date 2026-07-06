import os
import pandas as pd
import yfinance as yf
from typing import Dict, List, Tuple


def _try_download_with_fallback(ticker: str) -> Tuple[str, pd.DataFrame]:
    """
    嘗試下載股票歷史數據，若失敗或無數據，會自動嘗試台灣股市的 alternative 尾碼 (.TW <=> .TWO)。
    回傳 (實際成功的代號, K 線 DataFrame)。
    """
    # 1. 整理代號格式
    clean_ticker = ticker.strip()
    
    # 若無後置碼，預設為 .TW
    if "." not in clean_ticker:
        primary = clean_ticker + ".TW"
        alternatives = [clean_ticker + ".TWO"]
    else:
        primary = clean_ticker
        if clean_ticker.endswith(".TW"):
            alternatives = [clean_ticker[:-3] + ".TWO"]
        elif clean_ticker.endswith(".TWO"):
            alternatives = [clean_ticker[:-4] + ".TW"]
        else:
            alternatives = []
            
    # 2. 嘗試下載主代號
    try:
        stock = yf.Ticker(primary)
        df = stock.history(period="1y")
        if not df.empty:
            return primary, df
    except Exception:
        pass
        
    # 3. 嘗試下載備用代號
    for alt in alternatives:
        try:
            print(f"  -> 代號 {primary} 無數據，嘗試備用代號: {alt}...")
            stock = yf.Ticker(alt)
            df = stock.history(period="1y")
            if not df.empty:
                print(f"  -> 備用代號 {alt} 下載成功！")
                return alt, df
        except Exception:
            pass
            
    # 若皆失敗，回傳原始代號與空 DataFrame
    return primary, pd.DataFrame()


def download_stock_data(tickers: List[str]) -> Dict[str, pd.DataFrame]:
    """
    下載指定股票清單的近 200 筆交易日 K 線數據，支援自動校正台灣股市代號尾碼。
    
    Args:
        tickers: 股票代號清單，例如 ['1101.TW', '8432.TW']
        
    Returns:
        Dict[str, pd.DataFrame]: 鍵為輸入的股票代號，值為包含 K 線資料的 DataFrame
    """
    data = {}
    print(f"開始下載股票數據，共 {len(tickers)} 檔股票...")
    
    for ticker in tickers:
        try:
            print(f"下載中: {ticker}")
            actual_ticker, df = _try_download_with_fallback(ticker)
            
            if df.empty:
                print(f"警告: 股票 {ticker} (含備用代號) 未獲取到任何歷史數據。")
                continue
            
            # 排序並取最後的 200 筆交易日數據
            df = df.sort_index()
            if len(df) > 200:
                df = df.tail(200)
                
            data[ticker] = df
            print(f"成功下載 {ticker} (實際使用: {actual_ticker})，共 {len(df)} 筆交易記錄。")
        except Exception as e:
            print(f"下載股票 {ticker} 時發生錯誤: {e}")
            
    return data


def get_latest_prices(tickers: List[str], downloaded_data: Dict[str, pd.DataFrame] = None) -> Dict[str, float]:
    """
    獲取指定股票清單的最新收盤價。若已下載過 K 線數據，優先從中讀取最新價以加速執行。
    
    Args:
        tickers: 股票代號清單
        downloaded_data: 已下載的 K 線數據字典 (可選)
        
    Returns:
        Dict[str, float]: 鍵為輸入的股票代號，值為最新收盤價
    """
    prices = {}
    print("開始獲取最新收盤價...")
    
    for ticker in tickers:
        # 1. 優先從已下載的數據中獲取
        if downloaded_data and ticker in downloaded_data:
            df = downloaded_data[ticker]
            if not df.empty:
                prices[ticker] = float(df['Close'].iloc[-1])
                print(f"{ticker} 最新收盤價 (來自已下載數據): {prices[ticker]:.2f}")
                continue
                
        # 2. 若無已下載數據，則在線獲取
        try:
            actual_ticker, df = _try_download_with_fallback(ticker)
            if not df.empty:
                latest_price = float(df['Close'].iloc[-1])
                prices[ticker] = latest_price
                print(f"{ticker} 最新收盤價: {latest_price:.2f}")
            else:
                print(f"錯誤: 無法獲取 {ticker} 的最新收盤價")
        except Exception as e:
            print(f"獲取 {ticker} 最新價格時發生錯誤: {e}")
            
    return prices


if __name__ == "__main__":
    # 測試下載功能與自動校正 (8432.TW 應自動更正為 8432.TWO，3615.TW 應更正為 3615.TWO)
    test_tickers = ["1101.TW", "8432.TW", "3481.TW", "3615.TW"]
    
    # 1. 測試下載 K 線
    k_data = download_stock_data(test_tickers)
    print("\n--- 下載完成結果 ---")
    for ticker, df in k_data.items():
        print(f"{ticker} 歷史 K 線總筆數: {len(df)}，最新收盤價: {df['Close'].iloc[-1]:.2f}")
        
    # 2. 測試最新價格
    prices = get_latest_prices(test_tickers, downloaded_data=k_data)
    print("\n--- 最新價格結果 ---")
    print(prices)
