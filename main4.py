import requests
import serial
import os
import time
import threading
from flask import Flask, send_file, abort, render_template_string, jsonify
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# LINE Messaging API設定
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
ARDUINO_PORT = os.getenv('ARDUINO_PORT')
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Flaskアプリ設定
app = Flask(__name__)

# グローバル変数でデータを保存
current_data = {
    'raw_value': 0,
    'percentage': 0,
    'status': 'unknown',
    'last_update': None,
    'message': '起動中...',
    'character_message': 'システム起動中だよ〜！',
    'character_face': 'normal'
}

# HTML テンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AquaSync 水分監視システム</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f8f9fa;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .header .subtitle {
            font-size: 16px;
            opacity: 0.9;
            font-weight: 400;
        }
        .content {
            padding: 30px;
        }
        .main-content {
            margin-bottom: 30px;
        }
        .status-overview {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        .character-section {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
        }
        .character-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #2c3e50;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .character-face {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            margin: 0 auto 15px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            transition: all 0.3s ease;
        }
        .character-face-happy {
            background: linear-gradient(135deg, #ffb3d6 0%, #ffc9e0 100%);
            border: 3px solid #ff69b4;
            box-shadow: 0 0 15px rgba(255, 105, 180, 0.3);
        }
        .character-face-normal {
            background: linear-gradient(135deg, #e8d5ff 0%, #f0e6ff 100%);
            border: 3px solid #9575cd;
            box-shadow: 0 0 10px rgba(149, 117, 205, 0.2);
        }
        .character-face-sad {
            background: linear-gradient(135deg, #ffcccb 0%, #ffe4e1 100%);
            border: 3px solid #ff6b6b;
            box-shadow: 0 0 10px rgba(255, 107, 107, 0.2);
        }
        .face-eyes {
            position: absolute;
            top: 20px;
            width: 100%;
            display: flex;
            justify-content: space-around;
            padding: 0 15px;
        }
        .eye {
            width: 10px;
            height: 12px;
            background: #333;
            border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
            position: relative;
        }
        .eye::after {
            content: '';
            position: absolute;
            top: -3px;
            left: -2px;
            width: 14px;
            height: 6px;
            border: 2px solid #333;
            border-bottom: none;
            border-radius: 50% 50% 0 0;
        }
        .eye::before {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 3px;
            height: 3px;
            background: white;
            border-radius: 50%;
        }
        .face-cheeks {
            position: absolute;
            top: 30px;
            width: 100%;
            display: flex;
            justify-content: space-between;
            padding: 0 8px;
        }
        .cheek {
            width: 12px;
            height: 8px;
            background: rgba(255, 182, 193, 0.6);
            border-radius: 50%;
        }
        .face-mouth {
            position: absolute;
            bottom: 15px;
            left: 50%;
            transform: translateX(-50%);
        }
        .mouth-happy {
            width: 25px;
            height: 12px;
            border: 2px solid #333;
            border-top: none;
            border-radius: 0 0 25px 25px;
        }
        .mouth-normal {
            width: 16px;
            height: 2px;
            background: #333;
            border-radius: 2px;
        }
        .mouth-sad {
            width: 25px;
            height: 12px;
            border: 2px solid #333;
            border-bottom: none;
            border-radius: 25px 25px 0 0;
            transform: translateX(-50%) rotate(180deg);
        }
        .face-bow {
            position: absolute;
            top: -8px;
            left: 50%;
            transform: translateX(-50%);
            width: 16px;
            height: 8px;
        }
        .face-bow::before {
            content: '';
            position: absolute;
            left: 0;
            width: 6px;
            height: 8px;
            background: #ff69b4;
            border-radius: 50% 0 50% 50%;
            transform: rotate(-20deg);
        }
        .face-bow::after {
            content: '';
            position: absolute;
            right: 0;
            width: 6px;
            height: 8px;
            background: #ff69b4;
            border-radius: 0 50% 50% 50%;
            transform: rotate(20deg);
        }
        .face-bow-center {
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 4px;
            height: 6px;
            background: #e91e63;
            border-radius: 2px;
        }
        .character-message {
            background: linear-gradient(135deg, #fff0f5 0%, #ffeef8 100%);
            border: 1px solid #ffb3d6;
            border-radius: 15px;
            padding: 8px 12px;
            font-size: 12px;
            color: #8e24aa;
            font-weight: 500;
            position: relative;
            margin-top: 10px;
        }
        .character-message::before {
            content: '';
            position: absolute;
            top: -6px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-bottom: 6px solid #ffb3d6;
        }
        .character-message::after {
            content: '';
            position: absolute;
            top: -5px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-bottom: 5px solid #fff0f5;
        }
        .metric-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
        }
        .metric-icon {
            font-size: 24px;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
        }
        .metric-label {
            font-size: 14px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .main-status {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
        }
        .status-icon {
            font-size: 48px;
            margin-bottom: 20px;
        }
        .percentage {
            font-size: 56px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .status-message {
            font-size: 18px;
            margin-bottom: 25px;
            padding: 0 20px;
        }
        .progress-container {
            width: 100%;
            background: #e9ecef;
            border-radius: 4px;
            height: 12px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        .progress-fill {
            height: 100%;
            transition: width 0.5s ease;
            border-radius: 4px;
        }
        .status-green .metric-icon { color: #28a745; }
        .status-green .status-icon { color: #28a745; }
        .status-green .percentage { color: #28a745; }
        .status-green .progress-fill { background: #28a745; }
        
        .status-yellow .metric-icon { color: #ffc107; }
        .status-yellow .status-icon { color: #ffc107; }
        .status-yellow .percentage { color: #ffc107; }
        .status-yellow .progress-fill { background: #ffc107; }
        
        .status-red .metric-icon { color: #dc3545; }
        .status-red .status-icon { color: #dc3545; }
        .status-red .percentage { color: #dc3545; }
        .status-red .progress-fill { background: #dc3545; }
        
        .status-unknown .metric-icon { color: #6c757d; }
        .status-unknown .status-icon { color: #6c757d; }
        .status-unknown .percentage { color: #6c757d; }
        .status-unknown .progress-fill { background: #6c757d; }
        
        .actions {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 30px;
        }
        .btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background-color 0.2s;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn:hover {
            background: #0056b3;
        }
        .btn-secondary {
            background: #6c757d;
        }
        .btn-secondary:hover {
            background: #545b62;
        }
        .footer-info {
            background: #f8f9fa;
            padding: 20px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            font-size: 14px;
            color: #6c757d;
        }
        .footer-info i {
            margin-right: 5px;
        }
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            .status-overview {
                grid-template-columns: 1fr;
            }
            .actions {
                flex-direction: column;
                align-items: center;
            }
        }
    </style>
    <script>
        function refreshData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    // 基本データの更新
                    document.getElementById('percentage').textContent = data.percentage;
                    document.getElementById('percentage-main').textContent = data.percentage + '%';
                    document.getElementById('raw-value').textContent = data.raw_value;
                    document.getElementById('status-text').textContent = getStatusText(data.status);
                    document.getElementById('last-update').textContent = data.last_update || '未取得';
                    
                    // キャラクターの更新
                    document.getElementById('character-message').textContent = data.character_message || 'お疲れ様！';
                    updateCharacterFace(data.character_face || data.status);
                    
                    // ステータスに応じてクラスを更新
                    const mainStatus = document.getElementById('main-status');
                    const metricCards = document.querySelectorAll('.metric-card');
                    
                    // 古いステータスクラスを削除
                    mainStatus.className = 'main-status status-' + data.status;
                    metricCards.forEach(card => {
                        card.className = 'metric-card status-' + data.status;
                    });
                    
                    // プログレスバーを更新
                    const progressFill = document.getElementById('progress-fill');
                    progressFill.style.width = data.percentage + '%';
                    progressFill.className = 'progress-fill status-' + data.status;
                    
                    // ステータスアイコンを更新
                    const statusIcon = document.getElementById('status-icon');
                    statusIcon.className = getStatusIcon(data.status);
                });
        }
        
        function updateCharacterFace(faceType) {
            const face = document.getElementById('character-face');
            const mouth = document.getElementById('face-mouth');
            
            // クラスをリセット
            face.className = 'character-face';
            mouth.className = 'face-mouth';
            
            switch(faceType) {
                case 'green':
                case 'happy':
                    face.classList.add('character-face-happy');
                    mouth.classList.add('mouth-happy');
                    break;
                case 'red':
                case 'sad':
                    face.classList.add('character-face-sad');
                    mouth.classList.add('mouth-sad');
                    break;
                default:
                    face.classList.add('character-face-normal');
                    mouth.classList.add('mouth-normal');
                    break;
            }
        }
        
        function getStatusText(status) {
            switch(status) {
                case 'green': return '良好';
                case 'yellow': return '適度';
                case 'red': return '不足';
                default: return '不明';
            }
        }
        
        function getStatusIcon(status) {
            switch(status) {
                case 'green': return 'fas fa-check-circle status-icon';
                case 'yellow': return 'fas fa-exclamation-triangle status-icon';
                case 'red': return 'fas fa-times-circle status-icon';
                default: return 'fas fa-question-circle status-icon';
            }
        }
        
        // 15秒ごとに自動更新
        setInterval(refreshData, 15000);
        
        // ページ読み込み時に1回実行
        window.onload = refreshData;
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-seedling"></i> AquaSync 水分監視システム</h1>
            <div class="subtitle">植物の水分レベルをリアルタイムで監視</div>
        </div>
        
        <div class="content">
            <div class="status-overview">
                <div class="metric-card status-{{ status }}">
                    <div class="metric-icon">
                        <i class="fas fa-tint"></i>
                    </div>
                    <div class="metric-value" id="percentage">{{ percentage }}</div>
                    <div class="metric-label">水分レベル (%)</div>
                </div>
                
                <div class="metric-card status-{{ status }}">
                    <div class="metric-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="metric-value" id="raw-value">{{ raw_value }}</div>
                    <div class="metric-label">センサー値</div>
                </div>
                
                <div class="metric-card status-{{ status }}">
                    <div class="metric-icon">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    <div class="metric-value" id="status-text">
                        {% if status == 'green' %}良好
                        {% elif status == 'yellow' %}適度
                        {% elif status == 'red' %}不足
                        {% else %}不明{% endif %}
                    </div>
                    <div class="metric-label">ステータス</div>
                </div>
                
                <div class="character-section">
                    <div class="character-title">植物の気持ち</div>
                    <div id="character-face" class="character-face character-face-{{ character_face }}">
                        <div class="face-bow">
                            <div class="face-bow-center"></div>
                        </div>
                        <div class="face-eyes">
                            <div class="eye"></div>
                            <div class="eye"></div>
                        </div>
                        <div class="face-cheeks">
                            <div class="cheek"></div>
                            <div class="cheek"></div>
                        </div>
                        <div id="face-mouth" class="face-mouth 
                            {% if character_face == 'happy' or status == 'green' %}mouth-happy
                            {% elif character_face == 'sad' or status == 'red' %}mouth-sad
                            {% else %}mouth-normal{% endif %}">
                        </div>
                    </div>
                    <div class="character-message" id="character-message">
                        {{ character_message }}
                    </div>
                </div>
            </div>
            
            <div id="main-status" class="main-status status-{{ status }}">
                <div id="status-icon" class="
                    {% if status == 'green' %}fas fa-check-circle
                    {% elif status == 'yellow' %}fas fa-exclamation-triangle
                    {% elif status == 'red' %}fas fa-times-circle
                    {% else %}fas fa-question-circle{% endif %} status-icon">
                </div>
                
                <div class="percentage" id="percentage-main">{{ percentage }}%</div>
                
                <div class="progress-container">
                    <div id="progress-fill" class="progress-fill status-{{ status }}" 
                         style="width: {{ percentage }}%"></div>
                </div>
                
                <div class="status-message">
                    {% if status == 'green' %}
                        水分レベルは十分です。植物は健康な状態を保っています。
                    {% elif status == 'yellow' %}
                        水分レベルは適度です。継続的な監視をお勧めします。
                    {% elif status == 'red' %}
                        水分が不足しています。早急に水やりが必要です。
                    {% else %}
                        システムが起動中です。しばらくお待ちください。
                    {% endif %}
                </div>
            </div>
            
            <div class="actions">
                <button class="btn" onclick="refreshData()">
                    <i class="fas fa-sync-alt"></i> データを更新
                </button>
                <button class="btn btn-secondary" onclick="window.location.reload()">
                    <i class="fas fa-redo"></i> ページを再読み込み
                </button>
            </div>
        </div>
        
        <div class="footer-info">
            <i class="fas fa-clock"></i> 最終更新: <span id="last-update">{{ last_update or '未取得' }}</span>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """水分レベルダッシュボードを表示"""
    return render_template_string(HTML_TEMPLATE, **current_data)

@app.route('/api/data')
def get_data():
    """現在の水分データをJSON形式で返す"""
    return jsonify(current_data)

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

def generate_character_message(percentage, status):
    """Gemini APIを使って植物キャラクターのセリフを生成"""
    if not GEMINI_API_KEY:
        return get_default_message(status)
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')  # モデル名を更新
        
        # ギャルっぽいセリフ用のプロンプト
        prompt = f"""
あなたは明るくて元気なギャル系の植物キャラクターです。
現在の水分レベル: {percentage}%
状態: {status}

以下の条件でセリフを作ってください：
- 15文字以内の短いセリフ
- 明るくてギャルっぽい話し方
- 「〜だよ！」「〜じゃん！」「〜って感じ♪」などの語尾
- 絵文字は使わない
- 水分状態に応じた気持ちを表現

例：
良好な時: 「めっちゃ元気だよ〜！」
適度な時: 「まあまあって感じかな」
不足な時: 「のど乾いちゃった〜」

セリフのみを返してください:
"""
        
        response = model.generate_content(prompt)
        message = response.text.strip()
        
        # 長すぎる場合は切り詰め
        if len(message) > 20:
            message = message[:17] + "..."
            
        return message
        
    except Exception as e:
        print(f"Gemini API エラー: {e}")
        return get_default_message(status)

def get_default_message(status):
    """デフォルトメッセージ（API失敗時用）"""
    import random
    
    messages = {
        'green': [
            'めっちゃ元気だよ〜！',
            '今日も調子いいじゃん♪',
            'プリプリしてる〜！',
            'ウォーター満タンって感じ！',
            'キラキラしてるよ〜',
            '最高の気分だよ！',
            'ハッピーって感じ♪',
            'ツヤツヤでしょ〜？'
        ],
        'yellow': [
            'まあまあって感じかな',
            'ぼちぼちだよ〜',
            'そこそこって感じ！',
            'まずまずかな〜？',
            '普通って感じだよ',
            'まあ悪くないじゃん',
            'こんなもんかな〜',
            'いい感じかも？'
        ],
        'red': [
            'のど乾いちゃった〜',
            'お水欲しいよ〜！',
            'カラカラだよ〜',
            'ちょっと疲れたかも',
            'うるうるしたいな',
            '水分補給したい！',
            '乾燥しちゃう〜',
            '潤いが欲しいよ〜'
        ],
        'unknown': [
            'どうかな〜？',
            'よくわからないや',
            'どんな感じかな？',
            'チェック中だよ〜'
        ]
    }
    
    status_messages = messages.get(status, ['よろしく〜♪'])
    return random.choice(status_messages)

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

def update_current_data(raw_value, percentage):
    """現在のデータを更新"""
    global current_data
    
    if percentage <= 30:
        status = "red"
        face = "sad"
    elif percentage <= 60:
        status = "yellow"
        face = "normal"
    else:
        status = "green"
        face = "happy"
    
    # Gemini APIでキャラクターメッセージを生成
    character_message = generate_character_message(percentage, status)
    
    current_data.update({
        'raw_value': raw_value,
        'percentage': percentage,
        'status': status,
        'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'message': get_water_status_message(raw_value, percentage),
        'character_message': character_message,
        'character_face': face
    })
    
    print(f"📊 データ更新: {percentage}% ({status}) | キャラクター: {character_message}")

def send_status_report(raw_value, percentage, status_type):
    """状態に応じたLINE通知を送信"""
    message = get_water_status_message(raw_value, percentage)
    
    # Webダッシュボード用のデータも更新
    update_current_data(raw_value, percentage)
    
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
    print(f"Gemini API Key設定: {'OK' if GEMINI_API_KEY else 'NG'}")
    print(f"画像サーバーURL: {SERVER_URL}")
    
    if not CHANNEL_ACCESS_TOKEN:
        print("❌ CHANNEL_ACCESS_TOKENが設定されていません")
        return

    # 初期キャラクターメッセージ設定
    initial_message = generate_character_message(0, 'unknown')
    current_data['character_message'] = initial_message
    print(f"🎭 キャラクター初期化: {initial_message}")

    # Flaskサーバー起動
    print("🌐 Webダッシュボードサーバーを起動中...")
    flask_thread = threading.Thread(target=start_flask_server)
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(2)
    
    print("🌐 Webダッシュボード: http://localhost:5000")
    
    # LINE接続テスト
    if not test_line_connection():
        print("LINE接続に問題があります。続行しますが通知は送信されません。")
    
    print("✅ システム準備完了")
    print("📊 水分レベル変化と定期レポートでLINE通知を送信します")
    print("🎭 キャラクターが15秒ごとに気持ちを教えてくれます")
    
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
                        
                        # Webダッシュボードのデータを常時更新
                        update_current_data(raw_value, percentage)
                        
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