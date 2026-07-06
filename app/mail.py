import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from app import config


def send_email_report(html_content: str) -> bool:
    """
    使用 SMTP 將 HTML 報告發送至設定的收件人信箱。
    """
    # 1. 檢查郵件相關配置是否齊全
    if not all([config.SMTP_SERVER, config.SMTP_USER, config.SMTP_PASSWORD, config.RECIPIENT_EMAIL]):
        print("警告: 郵件發送設定不完整（SMTP_SERVER, SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAIL）。跳過郵件發送。")
        return False
        
    print(f"正在準備發送郵件報告至: {config.RECIPIENT_EMAIL} ...")
    
    # 2. 建立郵件訊息
    msg = MIMEMultipart("alternative")
    today_str = datetime.now().strftime("%Y-%m-%d")
    msg["Subject"] = f"[AI Stock Agent] 短線個股風險評估報告 - {today_str}"
    msg["From"] = config.SMTP_USER
    msg["To"] = config.RECIPIENT_EMAIL
    
    # 附加 HTML 內文
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    
    # 3. 建立 SMTP 連線並發送
    try:
        if config.SMTP_PORT == 465:
            # SSL 連線 (通常用於 465 端口)
            print(f"建立 SSL 連線 (SMTP: {config.SMTP_SERVER}:{config.SMTP_PORT})...")
            server = smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT, timeout=15)
        else:
            # TLS 連線 (通常用於 587 端口或其它)
            print(f"建立 TLS 連線 (SMTP: {config.SMTP_SERVER}:{config.SMTP_PORT})...")
            server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            
        print("登入 SMTP 伺服器...")
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        
        print("傳送郵件中...")
        server.sendmail(config.SMTP_USER, config.RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        
        print("郵件報告發送成功！")
        return True
    except Exception as e:
        print(f"郵件發送失敗: {e}")
        return False


if __name__ == "__main__":
    # 測試發送
    test_html = """
    <html>
    <body>
        <h1>AI Stock Agent SMTP 測試連線</h1>
        <p>這是一封來自 AI Stock Agent 的自動測試郵件，代表您的 SMTP 伺服器已成功連線！</p>
        <p>時間：{}</p>
    </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    print("=== SMTP 發送測試 ===")
    success = send_email_report(test_html)
    print("測試結果:", "成功" if success else "失敗")
