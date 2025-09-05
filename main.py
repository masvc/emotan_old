import requests
import serial
import os
import time
from dotenv import load_dotenv

load_dotenv()

LINE_TOKEN = os.getenv('LINE_TOKEN')
ARDUINO_PORT = os.getenv('ARDUINO_PORT')

def send_line_message(message):
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    data = {"message": message}
    try:
        response = requests.post(url, headers=headers, data=data)
        print(f"LINE送信: {response.status_code} - {message}")
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def main():
    print(f"Arduino監視開始: {ARDUINO_PORT}")
    try:
        arduino = serial.Serial(ARDUINO_PORT, 9600)
        time.sleep(2)
        
        while True:
            try:
                line = arduino.readline().decode().strip()
                if line:
                    print(f"受信: {line}")
                    if "NOTIFICATION:GREEN" in line:
                        send_line_message("🟢 植物の水分が適度になりました！")
            except KeyboardInterrupt:
                print("\n監視を終了します")
                break
            except Exception as e:
                print(f"読み取りエラー: {e}")
                time.sleep(1)
    except Exception as e:
        print(f"Arduino接続エラー: {e}")

if __name__ == "__main__":
    main()
