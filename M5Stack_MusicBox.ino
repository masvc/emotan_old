#include <M5Unified.h>

// 音符の定義
#define NOTE_C4  262
#define NOTE_D4  294
#define NOTE_E4  330
#define NOTE_F4  349
#define NOTE_G4  392
#define NOTE_A4  440
#define NOTE_B4  494
#define NOTE_C5  523
#define NOTE_D5  587
#define NOTE_E5  659
#define NOTE_F5  698
#define NOTE_G5  784

bool isPlaying = false;

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);
  
  // スピーカー設定
  M5.Speaker.begin();
  M5.Speaker.setVolume(200);
  
  M5.Display.fillScreen(BLACK);
  M5.Display.setTextColor(WHITE);
  M5.Display.setTextSize(2);
  M5.Display.setCursor(80, 40);
  M5.Display.println("Music Box");
  
  M5.Display.setTextSize(1);
  M5.Display.setCursor(10, 100);
  M5.Display.println("A: 現状のアリア");
  M5.Display.setCursor(10, 120);
  M5.Display.println("B: ストップ");
  M5.Display.setCursor(10, 140);
  M5.Display.println("C: きらきら星");
  
  M5.Display.setCursor(10, 180);
  M5.Display.setTextColor(YELLOW);
  M5.Display.println("Ready! ボタンを押してください");
}

void loop() {
  M5.update();
  
  if (M5.BtnA.wasPressed()) {
    playAria();
  }
  
  if (M5.BtnB.wasPressed()) {
    stopMusic();
  }
  
  if (M5.BtnC.wasPressed()) {
    playTwinkleTwinkle();
  }
  
  delay(100);
}

void playAria() {
  if (isPlaying) return;
  
  isPlaying = true;
  
  M5.Display.fillRect(10, 200, 300, 20, BLACK);
  M5.Display.setCursor(10, 200);
  M5.Display.setTextColor(CYAN);
  M5.Display.println("♪ G線上のアリア演奏中...");
  
  // バッハのG線上のアリア
  int aria[] = {
    NOTE_D4, NOTE_A4, NOTE_G4, NOTE_F4, NOTE_E4, NOTE_D4,
    NOTE_A4, NOTE_D5, NOTE_C5, NOTE_B4, NOTE_A4, NOTE_G4,
    NOTE_F4, NOTE_G4, NOTE_A4, NOTE_B4, NOTE_C5, NOTE_D5,
    NOTE_A4, NOTE_G4, NOTE_F4, NOTE_E4, NOTE_F4, NOTE_G4,
    NOTE_A4, NOTE_D4, NOTE_E4, NOTE_F4, NOTE_G4, NOTE_A4,
    NOTE_B4, NOTE_C5, NOTE_B4, NOTE_A4, NOTE_G4, NOTE_F4,
    NOTE_E4, NOTE_D4
  };
  
  int ariaDurations[] = {
    800, 400, 400, 400, 400, 800,
    600, 400, 400, 400, 400, 600,
    400, 400, 400, 400, 400, 800,
    600, 400, 400, 400, 400, 600,
    400, 400, 400, 400, 400, 600,
    400, 400, 400, 400, 400, 600,
    400, 1200
  };
  
  int ariaLength = sizeof(aria) / sizeof(aria[0]);
  
  for (int i = 0; i < ariaLength && isPlaying; i++) {
    M5.update();
    if (M5.BtnB.wasPressed()) {
      stopMusic();
      return;
    }
    
    M5.Speaker.tone(aria[i], ariaDurations[i]);
    delay(ariaDurations[i] + 100); // ゆったりとした演奏
  }
  
  isPlaying = false;
  M5.Display.fillRect(10, 200, 300, 20, BLACK);
  M5.Display.setCursor(10, 200);
  M5.Display.setTextColor(GREEN);
  M5.Display.println("♪ G線上のアリア完了");
}

void stopMusic() {
  isPlaying = false;
  M5.Speaker.stop();
  
  M5.Display.fillRect(10, 200, 300, 20, BLACK);
  M5.Display.setCursor(10, 200);
  M5.Display.setTextColor(RED);
  M5.Display.println("■ 停止しました");
  
  // 停止音
  M5.Speaker.tone(300, 200);
  delay(250);
}

void playTwinkleTwinkle() {
  if (isPlaying) return;
  
  isPlaying = true;
  
  M5.Display.fillRect(10, 200, 300, 20, BLACK);
  M5.Display.setCursor(10, 200);
  M5.Display.setTextColor(YELLOW);
  M5.Display.println("★ きらきら星演奏中...");
  
  // きらきら星のメロディー
  int twinkle[] = {
    NOTE_C4, NOTE_C4, NOTE_G4, NOTE_G4, NOTE_A4, NOTE_A4, NOTE_G4,
    NOTE_F4, NOTE_F4, NOTE_E4, NOTE_E4, NOTE_D4, NOTE_D4, NOTE_C4,
    NOTE_G4, NOTE_G4, NOTE_F4, NOTE_F4, NOTE_E4, NOTE_E4, NOTE_D4,
    NOTE_G4, NOTE_G4, NOTE_F4, NOTE_F4, NOTE_E4, NOTE_E4, NOTE_D4,
    NOTE_C4, NOTE_C4, NOTE_G4, NOTE_G4, NOTE_A4, NOTE_A4, NOTE_G4,
    NOTE_F4, NOTE_F4, NOTE_E4, NOTE_E4, NOTE_D4, NOTE_D4, NOTE_C4
  };
  
  int twinkleDurations[] = {
    400, 400, 400, 400, 400, 400, 800,
    400, 400, 400, 400, 400, 400, 800,
    400, 400, 400, 400, 400, 400, 800,
    400, 400, 400, 400, 400, 400, 800,
    400, 400, 400, 400, 400, 400, 800,
    400, 400, 400, 400, 400, 400, 800
  };
  
  int twinkleLength = sizeof(twinkle) / sizeof(twinkle[0]);
  
  for (int i = 0; i < twinkleLength && isPlaying; i++) {
    M5.update();
    if (M5.BtnB.wasPressed()) {
      stopMusic();
      return;
    }
    
    M5.Speaker.tone(twinkle[i], twinkleDurations[i]);
    delay(twinkleDurations[i] + 50);
  }
  
  isPlaying = false;
  M5.Display.fillRect(10, 200, 300, 20, BLACK);
  M5.Display.setCursor(10, 200);
  M5.Display.setTextColor(GREEN);
  M5.Display.println("Twinkle Star Complete");
}