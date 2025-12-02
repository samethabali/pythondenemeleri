import pyautogui
import time

print("Oto tıklayıcı başlatıldı. 3 saniye sonra çalışmaya başlayacak...")
print(60//2.8)
time.sleep(3)



while True:
    pyautogui.click()  # Mevcut mouse konumuna tıklar
    print("Tıklandı!")
    time.sleep(3) # 3 saniye bekle
