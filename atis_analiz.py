import cv2
import numpy as np

# --- Global Degiskenler ---
# Bu degiskenler mouse callback fonksiyonu tarafindan guncellenecek
merkez = None
noktalar = []
secim_asama = "merkez" # 'merkez' veya 'delikler'
cizim_img = None # Uzerine cizim yapilacak kopya resim

def nokta_sec(event, x, y, flags, param):
    """ Mouse tiklamalarini yoneten fonksiyon """
    global merkez, noktalar, secim_asama, cizim_img

    # Sadece sol tika odaklan
    if event == cv2.EVENT_LBUTTONDOWN:
        
        if secim_asama == "merkez":
            merkez = (x, y)
            print(f"Merkez secildi: {merkez}")
            
            # Gorsel geri bildirim: Merkeze bir arti koy (Mavi)
            cv2.drawMarker(cizim_img, merkez, (255, 0, 0), cv2.MARKER_CROSS, 20, 2)
            
            # Asamayi degistir
            secim_asama = "delikler"
            print("Simdi atis deliklerini secin. Bitince 'h' tusuna basin.")

        elif secim_asama == "delikler":
            noktalar.append([x, y])
            print(f"Delik eklendi: ({x}, {y})")
            
            # Gorsel geri bildirim: Delige bir daire ciz (Kirmizi)
            cv2.circle(cizim_img, (x, y), 10, (0, 0, 255), 2)

def teshis(noktalar, merkez):
    """
    Atis noktalarini ve hedef merkezini alarak hata teshisi yapar.
    Turkce karakter KULLANILMADAN yazilmistir.
    """
    if not noktalar:
        return ["Hic atis noktasi secilmedi."]

    # dx: pozitif = sag, negatif = sol
    dx = [(x - merkez[0]) for x, y in noktalar]
    # dy: pozitif = asagi, negatif = yukari (OpenCV'de Y asagi artar)
    dy = [(y - merkez[1]) for x, y in noktalar]

    ort_x = np.mean(dx)
    ort_y = np.mean(dy)

    esik = 15.0 # Hata payi (piksel)
    sonuc = []

    # Yatay Eksen Analizi (X)
    if ort_x > esik:
        sonuc.append(f"[SAGA] Vuruslar ortalamada {ort_x:.1f} piksel sagda.\n   -> Olasi Hata: Tetik parmagi tetige cok fazla girmis (sag el icin).")
    elif ort_x < -esik:
        sonuc.append(f"[SOLA] Vuruslar ortalamada {ort_x:.1f} piksel solda.\n   -> Olasi Hata: Tetik parmagi ucuyla basiliyor (sag el icin).")
    else:
        sonuc.append("[YATAY MERKEZ] Vuruslar yatay eksende iyi gruplanmis.")

    # Dikey Eksen Analizi (Y)
    if ort_y > esik:
        sonuc.append(f"[ASAGI] Vuruslar ortalamada {ort_y:.1f} piksel asagida.\n   -> Olasi Hata: Atis aninda namluyu asagi bastirma.")
    elif ort_y < -esik:
        sonuc.append(f"[YUKARI] Vuruslar ortalamada {ort_y:.1f} piksel yukarida.\n   -> Olasi Hata: Atis aninda irkilme veya nefes alirken ates etme.")
    else:
        sonuc.append("[DIKEY MERKEZ] Vuruslar dikey eksende iyi gruplanmis.")

    if abs(ort_x) <= esik and abs(ort_y) <= esik:
        sonuc = ["[MERKEZDE] Grupman hedef merkezinde. Teknik gayet iyi!"]

    return sonuc

def main():
    global cizim_img, merkez, noktalar, secim_asama
    
    # ---- KLASORDEKI TUM RESIMLERI YUKLE ----
    klasor = "img"
    uzantilar = (".jpg", ".jpeg", ".png", ".bmp")
    import os
    resimler = [os.path.join(klasor, f) for f in os.listdir(klasor) if f.lower().endswith(uzantilar)]
    resimler.sort()

    if not resimler:
        print("Hata: img klasorunde resim bulunamadi!")
        return

    index = 0  # Şu anki resim indexi

    def resmi_yukle():
        nonlocal index
        global cizim_img, merkez, noktalar, secim_asama
        orijinal_img = None
        merkez = None
        noktalar = []
        secim_asama = "merkez"

        img = cv2.imread(resimler[index])
        if img is None:
            print(f"Hata: {resimler[index]} yuklenemedi.")
            return False

        cizim_img = img.copy()
        orijinal_img = img.copy()
        print(f"\n--- Su anki resim: {resimler[index]} ---")
        print("1. Lutfen fare ile hedef MERKEZINE tiklayin.")
        return True

    # İlk resmi yükle
    if not resmi_yukle():
        return

    pencere_adi = "Atis Analizi - Secim Ekrani"
    cv2.namedWindow(pencere_adi)
    cv2.setMouseCallback(pencere_adi, nokta_sec)

    print("--- Tuslar ---")
    print(" h : Hesapla")
    print(" r : Reset")
    print(" n : Sıradaki resim")
    print(" q : Cikis")
    print("---------------")

    while True:
        cv2.imshow(pencere_adi, cizim_img)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        elif key == ord('r'):
            resmi_yukle()

        elif key == ord('h'):
            if merkez and noktalar:
                print("\n--- ANALIZ SONUCU ---")
                sonuclar = teshis(noktalar, merkez)
                for r in sonuclar:
                    print("- " + r)

                ort_x = int(np.mean([p[0] for p in noktalar]))
                ort_y = int(np.mean([p[1] for p in noktalar]))
                cv2.circle(cizim_img, (ort_x, ort_y), 10, (0, 255, 0), 3)
                print(f"Grupman merkezi (yesil): ({ort_x}, {ort_y})")
            else:
                print("Hata: Merkez veya atis noktaları eksik.")

        elif key == ord('n'):
            index = (index + 1) % len(resimler)  # Döngüsel geçiş (sondan sonra başa döner)
            resmi_yukle()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()