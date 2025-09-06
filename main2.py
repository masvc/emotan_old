import requests
import serial
import os
import time
import threading
from flask import Flask, send_file, abort
from dotenv import load_dotenv

load_dotenv()

# LINE Messaging API設定
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
ARDUINO_PORT = os.getenv('ARDUINO_PORT')
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')

# Flaskアプリ設定
app = Flask(__name__)

@app.route('/image/<filename>')
def serve_image(filename):
    """ローカル画像ファイルを配信"""
    image_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(image_path):
        return send_file(image_path)
    else:
        abort(404)

def start_flask_server():
    """Flaskサーバーをバックグラウンドで起動"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def send_line_message(message):
    """LINE Messaging API経由でメッセージ送信"""
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    
    data = {
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"LINE送信成功: {message}")
            return True
        else:
            print(f"LINE送信失敗: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"LINE送信エラー: {e}")
        return False

def send_line_message_with_image(text_message, image_url=None):
    """テキストと画像を同時送信"""
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    
    messages = [
        {
            "type": "text",
            "text": text_message
        }
    ]
    
    if image_url:
        messages.append({
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": image_url
        })
    
    data = {"messages": messages}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"LINE送信成功: {text_message}" + (f" + 画像: {image_url}" if image_url else ""))
            return True
        else:
            print(f"LINE送信失敗: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"LINE送信エラー: {e}")
        return False

def get_water_status_message(raw_value, percentage):
    """水分レベルに応じたLINEメッセージを生成"""
    current_time = time.strftime("%H:%M")
    
    if percentage <= 30:
        return f"🔴 植物の水分不足 ({current_time})\n💧 水分レベル: {percentage}%\n⚠️ 水やりが必要です！"
    elif percentage <= 60:
        return f"🟡 植物の水分は適度 ({current_time})\n💧 水分レベル: {percentage}%\n✅ 良好な状態です"
    else:
        return f"🟢 植物の水分は十分 ({current_time})\n💧 水分レベル: {percentage}%\n🎉 完璧な状態です！"

def send_status_report(raw_value, percentage, status_type):
    """状態に応じたLINE通知を送信"""
    message = get_water_status_message(raw_value, percentage)
    
    if status_type == "green":  # 十分な水分状態（60%以上）
        # ohana.pngファイルの存在確認
        image_path = os.path.join(os.getcwd(), "ohana.png")
        if os.path.exists(image_path) and SERVER_URL.startswith('https://'):
            image_url = f"{SERVER_URL}/image/ohana.png"
            print(f"画像送信準備: {image_path} -> {image_url}")
            success = send_line_message_with_image(message, image_url)
        else:
            if not os.path.exists(image_path):
                print(f"⚠️ 画像ファイルが見つかりません: {image_path}")
            if not SERVER_URL.startswith('https://'):
                print("⚠️ HTTPS URLが必要です")
            success = send_line_message(message)
    else:
        success = send_line_message(message)
    
    return success

def test_line_connection():
    """LINE接続テスト"""
    print("LINE Messaging API接続テスト中...")
    success = send_line_message("🌱 AquaSync水分監視システムが開始されました\n定期的に植物の状態をお知らせします")
    if success:
        print("✅ LINE接続成功")
    else:
        print("❌ LINE接続失敗")
    return success

def parse_arduino_data(line):
    """Arduinoからのデータを解析"""
    try:
        if "Raw:" in line and "%" in line:
            # "Raw: 32 -> 32% | 状態: 🟡 適度な水分 - OK" のような形式を解析
            parts = line.split("->")
            if len(parts) >= 2:
                raw_part = parts[0].split("Raw:")[-1].strip()
                percent_part = parts[1].split("%")[0].strip()
                
                raw_value = int(raw_part)
                percentage = int(percent_part)
                
                return raw_value, percentage
    except Exception as e:
        print(f"データ解析エラー: {e}")
    
    return None, None

def main():
    print(f"🌱 AquaSync 水分レベル監視システム 🌱")
    print(f"Arduino監視開始: {ARDUINO_PORT}")
    print(f"Channel Access Token設定: {'OK' if CHANNEL_ACCESS_TOKEN else 'NG'}")
    print(f"画像サーバーURL: {SERVER_URL}")
    
    if not CHANNEL_ACCESS_TOKEN:
        print("❌ CHANNEL_ACCESS_TOKENが設定されていません")
        return

    # Flaskサーバー起動
    print("🌐 画像配信サーバーを起動中...")
    flask_thread = threading.Thread(target=start_flask_server)
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(2)
    
    # LINE接続テスト
    if not test_line_connection():
        print("LINE接続に問題があります。続行しますが通知は送信されません。")
    
    print("✅ システム準備完了")
    print("📊 水分レベル変化と定期レポートでLINE通知を送信します")
    
    # 状態追跡変数
    last_status = None
    last_report_time = time.time()
    report_interval = 300  # 5分間隔での定期レポート
    
    try:
        arduino = serial.Serial(ARDUINO_PORT, 9600)
        time.sleep(2)
        print("Arduino接続成功！水分監視を開始します。")
        
        while True:
            try:
                line = arduino.readline().decode().strip()
                if line:
                    print(f"受信: {line}")
                    
                    # 水分データの解析
                    raw_value, percentage = parse_arduino_data(line)
                    if raw_value is not None and percentage is not None:
                        current_time = time.time()
                        
                        # 状態変化の検出
                        current_status = None
                        if percentage <= 30:
                            current_status = "red"
                        elif percentage <= 60:
                            current_status = "yellow"
                        else:
                            current_status = "green"
                        
                        # 状態が変わった場合に通知
                        if current_status != last_status and last_status is not None:
                            print(f"🔔 状態変化検出: {last_status} → {current_status}")
                            success = send_status_report(raw_value, percentage, current_status)
                            if success:
                                print("✅ 状態変化通知送信完了")
                            else:
                                print("❌ 状態変化通知送信失敗")
                        
                        last_status = current_status
                        
                        # 定期レポート（5分間隔）
                        if current_time - last_report_time >= report_interval:
                            print("📊 定期レポート送信中...")
                            message = f"📊 定期レポート\n{get_water_status_message(raw_value, percentage)}\n\n次回レポート: 5分後"
                            success = send_line_message(message)
                            if success:
                                print("✅ 定期レポート送信完了")
                                last_report_time = current_time
                            else:
                                print("❌ 定期レポート送信失敗")
                    
                    # 特定状態メッセージの検出（バックアップ）
                    if "🟡 適度な水分状態になりました" in line:
                        print("🔔 黄色状態検出！")
                        
                    elif "🟢 十分な水量になりました" in line:
                        print("🔔 緑状態検出！")
                        
            except KeyboardInterrupt:
                print("\n監視を終了します")
                break
            except UnicodeDecodeError as e:
                print(f"文字エンコードエラー: {e}")
                time.sleep(0.1)
            except Exception as e:
                print(f"読み取りエラー: {e}")
                time.sleep(1)
                
    except Exception as e:
        print(f"Arduino接続エラー: {e}")
        print("ポート名やArduino IDEのシリアルモニタが開いていないか確認してください。")

if __name__ == "__main__":
    main()