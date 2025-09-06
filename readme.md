# AquaSync - 植物水分監視システム

植物の水分状態をリアルタイムで監視し、LINE 通知でお知らせするスマート植物ケアシステムです。

## 概要

AquaSync は、Arduino ベースのセンサーシステムと Python による LINE 通知機能を組み合わせた植物監視システムです。水分レベルに応じて視覚的・聴覚的・触覚的なフィードバックを提供し、植物の健康状態を直感的に把握できます。

## 主な機能

### ハードウェア機能

- **水分センサー**: 土壌の水分レベルをリアルタイム監視
- **4 桁 LED ディスプレイ**: 水分パーセンテージを数値表示
- **トラフィックライト**: 状態を色で表示（赤・黄・緑）
- **ブザー**: 状態変化時の音声通知
- **サーボモーター**: 動きによる触覚フィードバック

### ソフトウェア機能

- **LINE 通知**: 状態変化時の自動通知
- **定期レポート**: 5 分間隔での現状報告
- **画像送信**: 良好な状態時に画像付き通知
- **静音起動**: 近隣に配慮した設計

## 水分状態の表示

| 水分レベル | LED 色        | ディスプレイ | 音     | 動作           |
| ---------- | ------------- | ------------ | ------ | -------------- |
| 0-30%      | 🔴 赤（点滅） | 数値点滅     | なし   | なし           |
| 30-60%     | 🟡 黄         | 数値表示     | 単発音 | 軽いサーボ動作 |
| 60%以上    | 🟢 緑         | 数値表示     | 2 回音 | サーボ動作     |

## 必要な機材

### ハードウェア

- keystudio Arduino Uno 互換ボード
- keystudio 水分センサー
- keystudio 4 桁 LED ディスプレイ（TM1637）
- keystudio トラフィックライトモジュール
- keystudio ブザーモジュール
- keystudio サーボモーター
- keystudio センサーシールド
- USB Type-C ケーブル

### ソフトウェア

- Arduino IDE
- Python 3.13+
- ngrok
- LINE Developers アカウント

## セットアップ手順

### 1. ハードウェア接続

```
A0: 水分センサー
A1: LED電源
A2: 赤LED
A3: 黄LED
A4: 緑LED
A5: LED GND

2,3,4: ブザー (G,U,S)
6: サーボモーター
10,11,12,13: ディスプレイ (CLK,DIO,VCC,GND)
```

### 2. Arduino 設定

1. Arduino IDE で TM1637 ライブラリをインストール
2. `AquaSync2.ino`をアップロード

### 3. Python 環境構築

```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### 4. LINE 設定

1. LINE Developers Console でチャネル作成
2. チャネルアクセストークンを取得
3. `.env`ファイルに設定

```env
CHANNEL_ACCESS_TOKEN=your_channel_access_token
ARDUINO_PORT=/dev/cu.usbmodem11101
SERVER_URL=https://your-ngrok-url.ngrok-free.app
```

### 5. ngrok 設定

```bash
# 別ターミナルで実行
ngrok http 5000

# 表示されたHTTPS URLを.envのSERVER_URLに設定
```

## 使用方法

### 1. システム起動

```bash
# Arduinoにコードアップロード済みの状態で
cd emo-tan
source venv/bin/activate
python main2.py
```

### 2. 動作確認

- 起動時に LED テスト（赤 → 黄 → 緑）
- ディスプレイに水分%表示
- 水分センサーに水をかけて状態変化を確認

### 3. LINE 通知

- 状態変化時に自動通知
- 5 分間隔で定期レポート
- 緑状態時に画像付き通知

## ファイル構成

```
emo-tan/
├── AquaSync2.ino          # Arduino制御コード
├── main2.py               # Python監視・通知システム
├── main.py                # 旧バージョン（参考用）
├── ohana.png              # LINE通知用画像
├── .env                   # 環境変数設定
├── requirements.txt       # Python依存関係
├── README.md              # このファイル
└── venv/                  # Python仮想環境
```

## 技術仕様

### Arduino 側

- 言語: C++ (Arduino IDE)
- ライブラリ: Servo, TM1637Display
- 通信: シリアル通信（9600bps）
- 電源: USB 5V

### Python 側

- 言語: Python 3.13+
- 主要ライブラリ: requests, pyserial, flask, python-dotenv
- 通信: LINE Messaging API, HTTP/HTTPS
- サーバー: Flask (開発用)

## トラブルシューティング

### Arduino 接続エラー

```bash
# ポート確認
ls /dev/cu.usbmodem*

# .envファイルのARDUINO_PORTを正しいポートに更新
```

### LINE 通知が届かない

- チャネルアクセストークンの確認
- ボットとの友だち登録確認
- ngrok URL の更新確認

### 画像送信失敗

- ohana.png ファイルの存在確認
- ngrok HTTPS URL の確認
- SERVER_URL の設定確認

## 開発履歴

- v1.0: 基本的な水分監視機能
- v2.0: 4 桁ディスプレイ追加
- v2.1: トラフィックライト統合
- v2.2: 静音起動対応
- v2.3: 水分レベルベース通知システム（main2.py）

## ライセンス

MIT License

## 作成者

植物愛好家 & IoT 開発者
