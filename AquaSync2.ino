#include <Servo.h>
#include <TM1637Display.h>

// === ピン定義 ===
const int PIN_WATER = A0;    // ウォーターセンサー
const int PIN_SERVO = 6;     // サーボモーター

// ブザー
const int PIN_BUZZER_GND = 2;    // ブザー G
const int PIN_BUZZER_VCC = 3;    // ブザー U  
const int PIN_BUZZER_SIG = 4;    // ブザー S

// トラフィックライト
const int PIN_LED_VCC = A1;      // LED電源
const int PIN_LED_RED = A2;      // 赤LED  
const int PIN_LED_YELLOW = A3;   // 黄LED
const int PIN_LED_GREEN = A4;    // 緑LED
const int PIN_LED_GND = A5;      // LED GND

// 4桁ディスプレイ
#define CLK 10
#define DIO 11
#define DISPLAY_VCC 12
#define DISPLAY_GND 13

Servo myServo;
TM1637Display display(CLK, DIO);

// === ウォーターセンサー校正値 ===
int WATER_DRY_RAW = 0;       // 乾燥時の生値（低い値）
int WATER_WET_RAW = 100;    // 水に触れた時の生値（高い値）

// === しきい値（%で設定）===
const int WATER_LOW_THRESHOLD = 30;     // これ以下→水不足（赤）
const int WATER_OK_THRESHOLD  = 60;     // これ以上→十分な水（緑）

// === 状態管理フラグ ===
bool playedAria = false; // 一度だけ再生用フラグ
int lastWaterStatus = -1; // 前回の水分状態（-1=初期状態）
// 状態定義: 0=赤(水不足), 1=黄(適度), 2=緑(十分)

void setup() {
  Serial.begin(9600);
  
  // ブザー電源ピン設定
  pinMode(PIN_BUZZER_GND, OUTPUT);
  pinMode(PIN_BUZZER_VCC, OUTPUT);
  pinMode(PIN_BUZZER_SIG, OUTPUT);
  digitalWrite(PIN_BUZZER_GND, LOW);   // GND
  digitalWrite(PIN_BUZZER_VCC, HIGH);  // VCC
  
  // LED電源とピン設定
  pinMode(PIN_LED_VCC, OUTPUT);
  pinMode(PIN_LED_GND, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  digitalWrite(PIN_LED_VCC, HIGH);  // LED電源ON
  digitalWrite(PIN_LED_GND, LOW);   // GND設定
  
  // ディスプレイ用電源ピン設定
  pinMode(DISPLAY_VCC, OUTPUT);
  pinMode(DISPLAY_GND, OUTPUT);
  digitalWrite(DISPLAY_VCC, HIGH);  // 5V出力
  digitalWrite(DISPLAY_GND, LOW);   // GND出力
  
  // サーボ初期化
  myServo.attach(PIN_SERVO);
  myServo.write(90); // 中立位置
  
  // ディスプレイ初期化
  delay(100); // 電源安定化
  display.setBrightness(0x05); // 明度設定
  
  // 全LED消灯
  setTrafficLight(0, 0, 0);
  
  Serial.println("=== AquaSync 完全システム開始 ===");
  testAllSystems(); // 全システムテスト（静音）
}

void loop() {
  int rawWater = analogRead(PIN_WATER);
  int waterPct = analogToPercent(rawWater);
  
  // 現在の水分状態を判定
  int currentStatus = getWaterStatusCode(waterPct);
  
  // 状態が変わった時の処理
  handleStatusChange(currentStatus, waterPct);
  
  showStatusOnDisplay(waterPct, currentStatus); // ディスプレイ更新
  showTrafficLight(currentStatus); // LED更新
  
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
    return 2; // 緑（十分）
  } else {
    return 1; // 黄（適度）
  }
}

// 状態変化時の処理
void handleStatusChange(int currentStatus, int waterPct) {
  if (currentStatus != lastWaterStatus) {
    switch (currentStatus) {
      case 0: // 赤（水不足）
        // 音なし
        Serial.println("🔴 水不足状態になりました");
        break;
        
      case 1: // 黄（適度）
        playSimpleBeep(); // 単発音
        Serial.println("🟡 適度な水分状態になりました");
        break;
        
      case 2: // 緑（十分）
        if (!playedAria) {
          playDoubleBeep(); // 2回ビープ音
          playedAria = true;
        }
        Serial.println("🟢 十分な水量になりました");
        break;
    }
  }
}

// トラフィックライト制御
void setTrafficLight(int red, int yellow, int green) {
  digitalWrite(PIN_LED_RED, red);
  digitalWrite(PIN_LED_YELLOW, yellow);
  digitalWrite(PIN_LED_GREEN, green);
}

// 状態に応じたLED表示
void showTrafficLight(int status) {
  switch (status) {
    case 0: // 水不足 - 赤点灯
      setTrafficLight(1, 0, 0);
      break;
    case 1: // 適度 - 黄点灯
      setTrafficLight(0, 1, 0);
      break;
    case 2: // 十分 - 緑点灯
      setTrafficLight(0, 0, 1);
      break;
    default:
      setTrafficLight(0, 0, 0);
      break;
  }
}

// ディスプレイに状態表示
void showStatusOnDisplay(int waterPct, int status) {
  // 水分%を表示
  if (waterPct == 100) {
    display.showNumberDec(100, false);
  } else {
    display.showNumberDec(waterPct, false);
  }
  
  // 水不足時は点滅表示
  static unsigned long lastBlink = 0;
  static bool blinkState = false;
  
  if (status == 0 && millis() - lastBlink > 500) {
    if (blinkState) {
      display.clear();
      setTrafficLight(0, 0, 0); // LED消灯
    } else {
      display.showNumberDec(waterPct, false);
      setTrafficLight(1, 0, 0); // 赤LED点灯
    }
    blinkState = !blinkState;
    lastBlink = millis();
  }
}

// 水分状態テキスト
String getWaterStatus(int waterPct) {
  if (waterPct <= WATER_LOW_THRESHOLD) {
    return "🔴 水不足 - 水を追加してください";
  } else if (waterPct >= WATER_OK_THRESHOLD) {
    return "🟢 十分な水量 - 良好";
  } else {
    return "🟡 適度な水分 - OK";
  }
}

// 全システムテスト（静音版）
void testAllSystems() {
  Serial.println("=== 全システムテスト開始 ===");
  
  // LEDテスト
  Serial.println("LEDテスト: 赤→黄→緑");
  setTrafficLight(1, 0, 0); delay(500);
  setTrafficLight(0, 1, 0); delay(500);
  setTrafficLight(0, 0, 1); delay(500);
  setTrafficLight(0, 0, 0); delay(500);
  
  // ディスプレイテスト
  Serial.println("ディスプレイテスト");
  display.showNumberDec(8888); delay(1000);
  for (int i = 3; i >= 1; i--) {
    display.showNumberDec(i);
    delay(500);
  }
  display.clear(); delay(500);
  
  // ブザーテストは削除（静かな起動）
  Serial.println("ブザー: 静音モード");
  
  Serial.println("=== 全システムテスト完了 ===");
}

// 単発ビープ音（黄色状態用）
void playSimpleBeep() {
  Serial.println("🔔 単発音");
  tone(PIN_BUZZER_SIG, 1000, 300); // 1000Hz、300ms
  
  // サーボを軽く動かす
  myServo.write(85);
  delay(150);
  myServo.write(95);
  delay(150);
  myServo.write(90); // 中立に戻す
  
  delay(300);
  noTone(PIN_BUZZER_SIG);
  Serial.println("🔔 単発音終了");
}

// 2回ビープ音（緑状態用）
void playDoubleBeep() {
  Serial.println("🔔 完了音（2回）");
  
  // 1回目のビープ
  tone(PIN_BUZZER_SIG, 1200, 300); // 高い音、300ms
  myServo.write(85);
  delay(150);
  myServo.write(95);
  delay(150);
  noTone(PIN_BUZZER_SIG);
  
  delay(200); // 間隔
  
  // 2回目のビープ
  tone(PIN_BUZZER_SIG, 1200, 300); // 高い音、300ms
  myServo.write(85);
  delay(150);
  myServo.write(95);
  delay(150);
  
  myServo.write(90); // 中立に戻す
  delay(300);
  noTone(PIN_BUZZER_SIG);
  Serial.println("🔔 完了音終了");
}