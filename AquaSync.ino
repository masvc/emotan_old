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