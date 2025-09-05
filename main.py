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
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')  # ngrok URL用

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
    """LINE Messaging API経由でブロードキャストメッセージ送信"""
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    
    # メッセージデータ構造
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

def send_line_image(image_url, preview_url=None):
    """LINE Messaging API経由で画像送信"""
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    
    # プレビュー画像URLが指定されていない場合は元画像を使用
    if preview_url is None:
        preview_url = image_url
    
    data = {
        "messages": [
            {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": preview_url
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"LINE画像送信成功: {image_url}")
            return True
        else:
            print(f"LINE画像送信失敗: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"LINE画像送信エラー: {e}")
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
    
    # 画像URLが指定されている場合は画像メッセージも追加
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

def send_line_push_message(user_id, message):
    """特定ユーザーにプッシュメッセージ送信（オプション）"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    
    data = {
        "to": user_id,
        "messages": [
            {
                "type": "text", 
                "text": message
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"プッシュメッセージエラー: {e}")
        return False

def test_line_connection():
    """LINE Messaging API接続テスト"""
    print("LINE Messaging API接続テスト中...")
    success = send_line_message("🧪 Arduino水分センサーシステムが開始されました")
    if success:
        print("✅ LINE接続成功")
    else:
        print("❌ LINE接続失敗 - トークンとボット設定を確認してください")
    return success

def test_image_sending():
    """ohana.png送信テスト"""
    print("ohana.png送信テスト中...")
    image_url = f"{SERVER_URL}/image/ohana.png"
    success = send_line_message_with_image("🌺 テスト画像です！", image_url)
    if success:
        print("✅ 画像送信成功")
    else:
        print("❌ 画像送信失敗")
    return success

def main():
    print(f"Arduino監視開始: {ARDUINO_PORT}")
    print(f"Channel Access Token設定: {'OK' if CHANNEL_ACCESS_TOKEN else 'NG'}")
    print(f"画像サーバーURL: {SERVER_URL}")
    
    if not CHANNEL_ACCESS_TOKEN:
        print("❌ CHANNEL_ACCESS_TOKENが設定されていません")
        print(".envファイルにCHANNEL_ACCESS_TOKEN=your_token_hereを追加してください")
        return

    # Flaskサーバーをバックグラウンドで起動
    print("🌐 画像配信サーバーを起動中...")
    flask_thread = threading.Thread(target=start_flask_server)
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(2)  # サーバー起動待ち
    
    # LINE接続テスト
    if not test_line_connection():
        print("LINE接続に問題があります。続行しますが通知は送信されません。")
    
    # 画像送信準備完了メッセージ
    if SERVER_URL.startswith('https://'):
        print("✅ 画像送信機能: 有効（緑状態検出時にohana.pngを送信）")
    else:
        print("⚠️ 画像送信機能: 無効（HTTPS URLが必要）")
    
    try:
        arduino = serial.Serial(ARDUINO_PORT, 9600)
        time.sleep(2)
        print("Arduino接続成功！緑/青状態になるとLINE通知します。")
        
        while True:
            try:
                line = arduino.readline().decode().strip()
                if line:
                    print(f"受信: {line}")
                    
                    # 緑状態の検出
                    if "🟢 適度な水分状態になりました" in line:
                        print("🔔 緑状態検出！LINE通知を送信中...")
                        # 画像付きメッセージを送信
                        if SERVER_URL.startswith('https://'):
                            image_url = f"{SERVER_URL}/image/ohana.png"
                            success = send_line_message_with_image(
                                "🟢 植物の水分が適度になりました！\n水やりのタイミングです。",
                                image_url
                            )
                        else:
                            success = send_line_message("🟢 植物の水分が適度になりました！\n水やりのタイミングです。")
                        
                        if success:
                            print("✅ LINE通知送信完了")
                        else:
                            print("❌ LINE通知送信失敗")
                    
                    # 青状態の検出
                    elif "🔵 十分な水量になりました" in line:
                        print("🔔 青状態検出！完了通知を送信中...")
                        success = send_line_message("🔵 水やり完了！\n十分な水量になりました。🎵")
                        if success:
                            print("✅ LINE通知送信完了")
                        else:
                            print("❌ LINE通知送信失敗")
                            
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