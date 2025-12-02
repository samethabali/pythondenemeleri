# main_v4_erp.py
import cv2
from pyzbar.pyzbar import decode
import threading
import time
from tkinter import *
from tkinter import ttk  # Daha modern görünümlü widget'lar için
from tkinter import font # Font ayarı için
import sys
import database as db

##########################
# GLOBALS
##########################
stop_camera = False
last_qr_data = None       # En son okunan QR verisi
current_product_id = None # Arayüzde seçili olan ürün ID'si

##########################
# VERİTABANI BAŞLAT
##########################
db.init_db()

##########################
# TKINTER ARAYÜZÜ
##########################

# --- Ana Pencere ---
root = Tk()
root.title("QR Envanter Sistemi")
root.geometry("600x450")

# --- Fontlar ---
title_font = font.Font(family="Arial", size=14, weight="bold")
label_font = font.Font(family="Arial", size=12)
data_font = font.Font(family="Arial", size=12, weight="bold")

# --- Arayüz Parçaları ---

# 1. ÜRÜN BİLGİ ÇERÇEVESİ
product_frame = ttk.Frame(root, padding="10")
product_frame.pack(fill="x", pady=10, padx=10)

ttk.Label(product_frame, text="OKUTULAN ÜRÜN", font=title_font).grid(row=0, column=0, columnspan=2, pady=10)

# ID
ttk.Label(product_frame, text="Ürün ID:", font=label_font).grid(row=1, column=0, sticky="w", padx=5)
product_id_label = ttk.Label(product_frame, text="---", font=data_font, foreground="blue")
product_id_label.grid(row=1, column=1, sticky="w", padx=5)

# İsim
ttk.Label(product_frame, text="Ürün Adı:", font=label_font).grid(row=2, column=0, sticky="w", padx=5)
product_name_label = ttk.Label(product_frame, text="---", font=data_font)
product_name_label.grid(row=2, column=1, sticky="w", padx=5)

# Fiyat
ttk.Label(product_frame, text="Fiyat:", font=label_font).grid(row=3, column=0, sticky="w", padx=5)
product_price_label = ttk.Label(product_frame, text="---", font=data_font)
product_price_label.grid(row=3, column=1, sticky="w", padx=5)

# Stok
ttk.Label(product_frame, text="Stok:", font=label_font).grid(row=4, column=0, sticky="w", padx=5)
product_stock_label = ttk.Label(product_frame, text="---", font=data_font)
product_stock_label.grid(row=4, column=1, sticky="w", padx=5)


# 2. AKSİYON ÇERÇEVESİ
action_frame = ttk.Frame(root, padding="10")
action_frame.pack(fill="x", pady=10, padx=10)

ttk.Label(action_frame, text="İŞLEMLER", font=title_font).pack(pady=5)

# Değer Giriş Kutusu
input_frame = ttk.Frame(action_frame)
input_frame.pack(pady=5)
ttk.Label(input_frame, text="Değer (Adet/Fiyat):", font=label_font).pack(side=LEFT, padx=5)
value_entry = ttk.Entry(input_frame, font=label_font, width=10)
value_entry.pack(side=LEFT)

# Butonlar
button_frame = ttk.Frame(action_frame)
button_frame.pack(pady=10)

stock_increase_btn = ttk.Button(button_frame, text="Stok Artır (+)", command=lambda: handle_stock_change(True))
stock_increase_btn.pack(side=LEFT, padx=5, ipady=5)

stock_decrease_btn = ttk.Button(button_frame, text="Stok Azalt (-)", command=lambda: handle_stock_change(False))
stock_decrease_btn.pack(side=LEFT, padx=5, ipady=5)

price_update_btn = ttk.Button(button_frame, text="Fiyat Güncelle", command=lambda: handle_price_update())
price_update_btn.pack(side=LEFT, padx=5, ipady=5)


# 3. DURUM BİLGİSİ ÇERÇEVESİ
status_label = ttk.Label(root, text="Sistem Hazır. QR Kod Bekleniyor...", font=label_font, relief="sunken", anchor="center")
status_label.pack(fill="x", side=BOTTOM, ipady=5)


##########################
# ARAYÜZ FONKSİYONLARI
##########################

def show_status(message, is_error=False):
    """Durum çubuğunu günceller."""
    status_label.config(text=message, foreground="red" if is_error else "green")

def refresh_product_display(product_data):
    """Arayüzdeki ürün etiketlerini günceller."""
    global current_product_id
    if product_data:
        pid, name, price, stock = product_data
        current_product_id = pid # Butonların kullanması için global ID'yi ayarla
        product_id_label.config(text=pid)
        product_name_label.config(text=name)
        product_price_label.config(text=f"{price:.2f} TL")
        product_stock_label.config(text=str(stock))
        show_status(f"Ürün yüklendi: {name}")
    else:
        current_product_id = None
        product_id_label.config(text="BULUNAMADI")
        product_name_label.config(text="---")
        product_price_label.config(text="---")
        product_stock_label.config(text="---")
        show_status("Okutulan QR veritabanında bulunamadı.", is_error=True)

def refresh_data_after_update():
    """Butonla yapılan bir güncelleme sonrası veriyi tazeler."""
    if current_product_id:
        product_data = db.get_product(current_product_id)
        refresh_product_display(product_data) # Sadece etiketleri güncelle, status mesajı basma
        value_entry.delete(0, END) # Giriş kutusunu temizle

def handle_stock_change(is_increase):
    """'Stok Artır' veya 'Stok Azalt' butonu mantığı."""
    if not current_product_id:
        show_status("Önce bir ürün okutmalısınız!", is_error=True)
        return
        
    try:
        amount = int(value_entry.get())
        if amount <= 0:
            show_status("Değer 0'dan büyük olmalı!", is_error=True)
            return
    except ValueError:
        show_status("Lütfen geçerli bir sayı girin!", is_error=True)
        return

    # Azaltma ise değeri negatife çevir
    if not is_increase:
        amount = -amount

    success = db.modify_stock(current_product_id, amount)
    
    if success:
        show_status(f"Stok başarıyla güncellendi.", is_error=False)
        refresh_data_after_update()
    else:
        show_status("Stok güncellenemedi (Stok eksiye düşemez!)", is_error=True)

def handle_price_update():
    """'Fiyat Güncelle' butonu mantığı."""
    if not current_product_id:
        show_status("Önce bir ürün okutmalısınız!", is_error=True)
        return
        
    try:
        new_price = float(value_entry.get())
        if new_price < 0:
            show_status("Fiyat 0'dan küçük olamaz!", is_error=True)
            return
    except ValueError:
        show_status("Lütfen geçerli bir fiyat girin (örn: 25.50)!", is_error=True)
        return

    success = db.update_price(current_product_id, new_price)
    
    if success:
        show_status(f"Fiyat başarıyla güncellendi.", is_error=False)
        refresh_data_after_update()
    else:
        show_status("Fiyat güncellenemedi!", is_error=True)

##########################
# KAMERA DÖNGÜSÜ
##########################
cap = cv2.VideoCapture(0)

def qr_loop():
    global stop_camera, last_qr_data

    while not stop_camera:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        codes = decode(gray)
        
        detected_code_data = None
        
        if codes:
            # Sadece ilk algılanan kodu al
            code = codes[0]
            (x, y, w, h) = code.rect
            qr_data = code.data.decode("utf-8")
            detected_code_data = qr_data
            
            # Kamerada kutu çiz
            color = (0, 255, 0) if qr_data != last_qr_data else (0, 255, 255) # Yeni QR ise yeşil, aynıysa sarı
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
            
            # İsteğe bağlı: QR verisini kamerada göster
            # cv2.putText(frame, qr_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


        # İstek 1: Sadece YENİ bir QR kod okutulursa işlem yap
        if detected_code_data and detected_code_data != last_qr_data:
            last_qr_data = detected_code_data
            
            # İstek 2: Otomatik stok azaltma KALDIRILDI. Sadece bilgiyi çek.
            product_data = db.get_product(detected_code_data)
            
            # İstek 3: Bilgiyi statik olarak ekrana yansıt (thread-safe)
            root.after(0, lambda p=product_data: refresh_product_display(p))

        # Kamera penceresini göster (PC'de test için)
        cv2.imshow("KAMERA (Cikmak icin ESC)", frame)

        # ESC tuşu ile çıkış
        if cv2.waitKey(1) & 0xFF == 27:
            stop_camera = True
            break
        
    cap.release()
    cv2.destroyAllWindows()
    print("Kamera döngüsü durdu.")
    
    # ESC'ye basıldığında Tkinter'ı da kapat
    try:
        root.quit()
    except:
        pass

##########################
# GÜVENLİ KAPANMA (TKINTER 'X' BUTONU)
##########################
def on_closing():
    global stop_camera
    print("Kapatma sinyali alındı (X)...")
    stop_camera = True
    
    print("Kamera thread'inin bitmesi bekleniyor...")
    camera_thread.join(timeout=2.0)
    print("Thread kapandı. Çıkılıyor.")
    root.destroy()
    sys.exit()

root.protocol("WM_DELETE_WINDOW", on_closing)

##########################
# THREAD BAŞLAT
##########################
camera_thread = threading.Thread(target=qr_loop, daemon=True)
camera_thread.start()

##########################
# TKINTER ANA DÖNGÜ
##########################
root.mainloop()