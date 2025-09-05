# AquaSync 水分監視システム セットアップマニュアル

## 概要

Arduino 水分センサーと LINE 通知を組み合わせた植物監視システムです。水分状態に応じて LED で表示し、LINE Messaging API で画像付き通知を送信します。

## 📋 必要な機材・ソフトウェア

### ハードウェア

- Arduino Uno (Keystudio 互換ボード)
- 水分センサー
- サーボモーター
- パッシブブザー
- LED モジュール（赤・緑・青）
- USB Type-C ケーブル

### ソフトウェア

- Arduino IDE
- Python 3.13+
- ngrok
- LINE 公式アカウント

## 🔧 1. Arduino 設定

### 1.1 Arduino IDE インストール

1. [Arduino IDE](https://www.arduino.cc/en/software)をダウンロード・インストール
2. Arduino Uno を USB で接続
3. ツール → ボード → Arduino Uno を選択
4. ツール → ポート → 適切なポートを選択

### 1.2 Arduino コード

以下のコードを Arduino IDE に貼り付けてアップロード：

```cpp
#include <Servo.h>

// === ピン定義 ===
const int PIN_WATER = A0;    // ウォーターセンサー
const int PIN_SERVO = 6;     // サーボモーター
const int PIN_BUZZER = 2;    // Passive Buzzer

// Traffic Light (4ピンモジュール)
const int PIN_RED   = 10;
const int PIN_GREEN = 11;
const int PIN_BLUE  = 12;
const int PIN_GND   = 13;

Servo myServo;

// === ウォーターセンサー校正値 ===
int WATER_DRY_RAW = 0;       // 乾燥時の生値（低い値）
int WATER_WET_RAW = 100;    // 水に触れた時の生値（高い値）

// === しきい値（%で設定）===
const int WATER_LOW_THRESHOLD = 30;     // これ以下→水不足（赤）
const int WATER_OK_THRESHOLD  = 60;     // これ以上→十分な水（青）

// === G線上のアリア（簡易メロディ） ===
int melody[] = {
  392, 440, 494, 523, 587, 494, 440, 392,
  392, 440, 494, 523, 494, 440, 392
};
int noteDurations[] = {
  600, 600, 600, 600, 600, 600, 600, 800,
  600, 600, 600, 600, 600, 600, 1200
};

// === 緑状態用の音（軽やかなメロディ） ===
int greenMelody[] = {
  523, 587, 659, 698  // ド、レ、ミ、ファ
};
int greenNoteDurations[] = {
  300, 300, 300, 400
};

// === 状態管理フラグ ===
bool playedAria = false; // 一度だけ再生用フラグ
int lastWaterStatus = -1; // 前回の水分状態（-1=初期状態）
// 状態定義: 0=赤(水不足), 1=緑(適度), 2=青(十分)

void setup() {
  Serial.begin(9600);

  // LED初期化
  pinMode(PIN_RED, OUTPUT);
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_BLUE, OUTPUT);
  pinMode(PIN_GND, OUTPUT);
  digitalWrite(PIN_GND, LOW);

  // サーボ初期化
  myServo.attach(PIN_SERVO);
  myServo.write(90); // 中立位置

  // 全LED消灯
  digitalWrite(PIN_RED, LOW);
  digitalWrite(PIN_GREEN, LOW);
  digitalWrite(PIN_BLUE, LOW);

  Serial.println("=== AquaSync システム開始 ===");
  testAllColors();
}

void loop() {
  int rawWater = analogRead(PIN_WATER);
  int waterPct = analogToPercent(rawWater);

  // 現在の水分状態を判定
  int currentStatus = getWaterStatusCode(waterPct);

  // 状態が変わった時の音楽処理
  handleStatusChange(currentStatus, waterPct);

  showTrafficLight(waterPct);

  Serial.print("Raw: ");
  Serial.print(rawWater);
  Serial.print(" -> ");
  Serial.print(waterPct);
  Serial.print("% | 状態: ");
  Serial.println(getWaterStatus(waterPct));

  // 前回の状態を更新
  lastWaterStatus = currentStatus;

  delay(1000);
}

// アナログ値をパーセントに変換
int analogToPercent(int rawValue) {
  int percent = map(rawValue, WATER_DRY_RAW, WATER_WET_RAW, 0, 100);
  return constrain(percent, 0, 100);
}

// 水分状態コードを取得
int getWaterStatusCode(int waterPct) {
  if (waterPct <= WATER_LOW_THRESHOLD) {
    return 0; // 赤（水不足）
  } else if (waterPct >= WATER_OK_THRESHOLD) {
    return 2; // 青（十分）
  } else {
    return 1; // 緑（適度）
  }
}

// 状態変化時の音楽処理
void handleStatusChange(int currentStatus, int waterPct) {
  // 状態が変わった時のみ音を鳴らす
  if (currentStatus != lastWaterStatus) {
    switch (currentStatus) {
      case 0: // 赤（水不足）
        // 赤の時は音なし（静寂で水不足を表現）
        Serial.println("🔴 水不足状態になりました");
        break;

      case 1: // 緑（適度）
        playGreenSound(); // 軽やかな音
        Serial.println("🟢 適度な水分状態になりました");
        break;

      case 2: // 青（十分）
        if (!playedAria) {
          playAria(); // G線上のアリア
          playedAria = true;
        }
        Serial.println("🔵 十分な水量になりました");
        break;
    }
  }
}

// LED制御
void showTrafficLight(int waterPct) {
  digitalWrite(PIN_RED, LOW);
  digitalWrite(PIN_GREEN, LOW);
  digitalWrite(PIN_BLUE, LOW);

  if (waterPct <= WATER_LOW_THRESHOLD) {
    digitalWrite(PIN_RED, HIGH);
  } else if (waterPct >= WATER_OK_THRESHOLD) {
    digitalWrite(PIN_BLUE, HIGH);
  } else {
    digitalWrite(PIN_GREEN, HIGH);
  }
}

// 水分状態テキスト
String getWaterStatus(int waterPct) {
  if (waterPct <= WATER_LOW_THRESHOLD) {
    return "🔴 水不足 - 水を追加してください";
  } else if (waterPct >= WATER_OK_THRESHOLD) {
    return "🔵 十分な水量 - 良好";
  } else {
    return "🟢 適度な水分 - OK";
  }
}

// LEDテスト
void testAllColors() {
  Serial.println("LEDテスト開始...");
  digitalWrite(PIN_RED, HIGH); delay(500); digitalWrite(PIN_RED, LOW);
  digitalWrite(PIN_GREEN, HIGH); delay(500); digitalWrite(PIN_GREEN, LOW);
  digitalWrite(PIN_BLUE, HIGH); delay(500); digitalWrite(PIN_BLUE, LOW);
  Serial.println("LEDテスト完了");
}

// 緑状態用の軽やかな音
void playGreenSound() {
  Serial.println("🎵 適度な水分メロディ演奏 🎵");
  for (int thisNote = 0; thisNote < sizeof(greenMelody)/sizeof(int); thisNote++) {
    int noteDuration = greenNoteDurations[thisNote];
    tone(PIN_BUZZER, greenMelody[thisNote], noteDuration);

    // サーボを軽く揺らす
    myServo.write(85);
    delay(noteDuration / 2);
    myServo.write(95);

    delay(noteDuration);
    noTone(PIN_BUZZER);
    delay(30);
  }
  myServo.write(90); // 中立に戻す
  Serial.println("🎵 適度メロディ終了 🎵");
}

// G線上のアリア演奏
void playAria() {
  Serial.println("🎵 G線上のアリアを演奏開始 🎵");
  for (int thisNote = 0; thisNote < sizeof(melody)/sizeof(int); thisNote++) {
    int noteDuration = noteDurations[thisNote];
    tone(PIN_BUZZER, melody[thisNote], noteDuration);

    // サーボをちょっと揺らす
    myServo.write(70);
    delay(noteDuration / 2);
    myServo.write(110);

    delay(noteDuration);
    noTone(PIN_BUZZER);
    delay(50);
  }
  myServo.write(90); // 中立に戻す
  Serial.println("🎵 演奏終了 🎵");
}
```

## 📱 2. LINE Messaging API 設定

### 2.1 LINE 公式アカウント作成

1. [LINE Developers Console](https://developers.line.biz/)にアクセス
2. LINE アカウントでログイン
3. 「新規チャネル作成」→「Messaging API」を選択
4. 必要情報を入力してチャネル作成

### 2.2 チャネルアクセストークン取得

1. 作成したチャネルの「Messaging API 設定」タブに移動
2. 「チャネルアクセストークン」の「発行」ボタンをクリック
3. 発行されたトークンをコピー（後で使用）

### 2.3 Webhook と応答設定

1. 「応答設定」で以下を設定：
   - 応答メッセージ：利用しない
   - Webhook：利用しない
2. ボットと友だちになる（QR コードから）

## 💻 3. Python 環境構築

### 3.1 プロジェクトディレクトリ作成

```bash
mkdir aquasync-project
cd aquasync-project
```

### 3.2 仮想環境とライブラリ

```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 必要ライブラリインストール
pip install requests==2.31.0 pyserial==3.5 python-dotenv==1.0.0 flask==3.0.0
```

### 3.3 設定ファイル作成

`.env`ファイルを作成：

```
CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
ARDUINO_PORT=/dev/cu.usbmodem11401
SERVER_URL=http://localhost:5000
```

### 3.4 メインプログラム

`main.py`に提供された Python コードを保存

### 3.5 画像ファイル配置

通知で送信したい画像（例：`ohana.png`）をプロジェクトディレクトリに配置

## 🌐 4. ngrok 設定（画像送信用）

### 4.1 ngrok インストール

```bash
# macOS (Homebrew)
brew install ngrok

# Windows/Linux: https://ngrok.com/download からダウンロード
```

### 4.2 ngrok アカウント設定（オプション）

1. [ngrok.com](https://ngrok.com/)でアカウント作成
2. 認証トークン取得してローカル設定

```bash
ngrok authtoken YOUR_AUTH_TOKEN
```

### 4.3 ngrok 起動

```bash
# ターミナルを新しく開いて実行
ngrok http 5000
```

表示された HTTPS URL（例：`https://abcd1234.ngrok.io`）をコピー

### 4.4 .env 更新

```
SERVER_URL=https://abcd1234.ngrok.io
```

## 🚀 5. システム起動

### 5.1 実行順序

1. **Arduino コードアップロード完了**
2. **ngrok 起動**（別ターミナル）

```bash
ngrok http 5000
```

3. **.env 更新**（ngrok の HTTPS URL）

4. **Python プログラム実行**

```bash
python main.py
```

### 5.2 正常起動の確認

```
Arduino監視開始: /dev/cu.usbmodem11401
Channel Access Token設定: OK
画像サーバーURL: https://abcd1234.ngrok.io
🌐 画像配信サーバーを起動中...
LINE Messaging API接続テスト中...
LINE送信成功: 🧪 Arduino水分センサーシステムが開始されました
✅ LINE接続成功
✅ 画像送信機能: 有効（緑状態検出時にohana.pngを送信）
Arduino接続成功！緑/青状態になるとLINE通知します。
```

## 📊 6. 動作確認

### 6.1 状態テスト

- **乾燥状態**：赤 LED、音なし
- **適度な湿度**（30-60%）：緑 LED、軽快な音楽、LINE 通知（画像付き）
- **十分な湿度**（60%以上）：青 LED、G 線上のアリア、LINE 通知

### 6.2 LINE 通知確認

- システム開始時：テキスト通知
- 緑状態：画像付き通知
- 青状態：完了通知

## ⚠️ 7. トラブルシューティング

### 7.1 Arduino 接続エラー

```
Arduino接続エラー: [Errno 16] Resource busy
```

**対処法**：Arduino IDE のシリアルモニタを閉じる

### 7.2 LINE 送信エラー

```
LINE送信失敗: 401 - Unauthorized
```

**対処法**：チャネルアクセストークンを確認

### 7.3 画像送信失敗

```
LINE画像送信失敗: 400 - Bad Request
```

**対処法**：

- ngrok が正常に動作しているか確認
- SERVER_URL が HTTPS で始まっているか確認
- 画像ファイルが存在するか確認

### 7.4 ポート確認

```bash
# 利用可能なポート確認
ls /dev/cu.usbmodem*

# プロセス確認
lsof /dev/cu.usbmodem11401
```

## 💡 8. 運用のコツ

### 8.1 常時運用

- PC 起動時に ngrok と Python スクリプトを自動実行
- systemd や launchd で自動起動設定

### 8.2 メッセージ制限

- LINE Messaging API：月 200 メッセージ（無料プラン）
- 頻繁な通知を避けるため状態変化時のみ送信

### 8.3 セキュリティ

- `.env`ファイルを Gitignore に追加
- チャネルアクセストークンを適切に管理

## 📝 9. カスタマイズ

### 9.1 しきい値調整

```cpp
const int WATER_LOW_THRESHOLD = 30;  // 水不足ライン
const int WATER_OK_THRESHOLD  = 60;  // 十分ライン
```

### 9.2 画像変更

- `ohana.png`を任意の画像に変更
- ファイル名をコードで更新

### 9.3 メッセージカスタマイズ

- LINE 通知のテキストを変更
- 絵文字や改行を調整

---

## ⚡ クイックスタート

1. Arduino IDE → コードアップロード
2. `pip install -r requirements.txt`
3. `.env`設定（LINE トークン）
4. `ngrok http 5000` → HTTPS URL 取得
5. `.env`更新（ngrok URL）
6. `python main.py`

システムが正常に起動すれば、LINE に開始通知が届きます。
