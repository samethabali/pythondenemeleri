from pynput import mouse, keyboard
import pyautogui
import threading
import time

# Veri yapısı: ('type', x/key, y/None, timestamp)
actions = []
recording = False
playing = False
start_time = 0

def on_click(x, y, button, pressed):
    if recording and pressed:
        elapsed = time.time() - start_time
        actions.append(('click', x, y, elapsed))
        print(f"[TIK] -> {x}, {y} ({elapsed:.2f}s)")

def on_press(key):
    global recording, playing, start_time

    # F9: Kaydı Başlat / Durdur
    if key == keyboard.Key.f9:
        if playing:
            return
            
        recording = not recording
        if recording:
            actions.clear()
            start_time = time.time()
            print("\n[KAYIT BASLADI] Hareketlerin kaydediliyor...")
        else:
            print("[KAYIT DURDU] Hafizaya alindi.")

    # F10: Oynatmayı Başlat / Durdur
    elif key == keyboard.Key.f10:
        if recording:
            return

        if not playing:
            playing = True
            print("\n[OYNATMA BASLADI] Durdurmak icin F10 veya ESC bas...")
            threading.Thread(target=replay, daemon=True).start()
        else:
            playing = False
            print("[OYNATMA DURDURULUYOR]...")

    # ESC: Çıkış
    elif key == keyboard.Key.esc:
        playing = False
        recording = False
        print("\n[CIKIS] Program kapatiliyor...")
        return False

    # Tuşları Kaydet
    elif recording:
        elapsed = time.time() - start_time
        try:
            key_val = key.char if hasattr(key, 'char') else str(key)
            actions.append(('key', key_val, None, elapsed))
            print(f"[TUS] -> {key_val}")
        except:
            pass

def replay():
    global playing
    
    while playing:
        if not actions:
            print("[UYARI] Oynatilacak kayit yok!")
            playing = False
            break

        start_replay_time = time.time()
        
        for action in actions:
            if not playing: break

            act_type, val1, val2, rec_time = action
            
            current_elapsed = time.time() - start_replay_time
            wait_time = rec_time - current_elapsed
            
            if wait_time > 0:
                time.sleep(wait_time)

            if act_type == 'click':
                pyautogui.click(x=val1, y=val2)
            elif act_type == 'key':
                key_str = str(val1).replace('Key.', '')
                
                if len(key_str) == 1:
                    pyautogui.write(key_str)
                else:
                    if key_str == 'space': pyautogui.press('space')
                    elif key_str == 'enter': pyautogui.press('enter')
                    elif key_str == 'backspace': pyautogui.press('backspace')
                    elif key_str == 'tab': pyautogui.press('tab')
                    elif key_str == 'esc': pyautogui.press('esc')
                    else: pyautogui.press(key_str)
        
        time.sleep(1)

# Dinleyiciler
print("KONTROLLER: F9: Kayit | F10: Oynat/Durdur | ESC: Cikis")

# Hata yönetimi eklenmiş listener başlatma
try:
    with mouse.Listener(on_click=on_click) as m_listener, \
         keyboard.Listener(on_press=on_press) as k_listener:
        k_listener.join()
except Exception as e:
    print(f"Bir hata olustu: {e}")
