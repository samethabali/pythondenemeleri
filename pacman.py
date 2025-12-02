import pygame
import sys
import random

# --- AYARLAR ---
GENISLIK, YUKSEKLIK = 600, 400 # Pencere boyutu
BLOCK_BOYUT = 20 # Her bir karenin piksel boyutu
HIZ = 4 # Pacman hızı

# Renkler (RGB)
SIYAH = (0, 0, 0)
MAVI = (0, 0, 255) # Duvarlar
SARI = (255, 255, 0) # Pacman
KIRMIZI = (255, 0, 0) # Hayaletler
BEYAZ = (255, 255, 255) # Yemler

# Harita Tasarımı (1: Duvar, 0: Yem, 2: Pacman, 3: Hayalet)
# Daha büyük harita için burayı uzatabilirsin
HARITA = [
    "111111111111111111111111111111",
    "120000000000011000000000000001",
    "101111011111011011111011111101",
    "101000000000000000000000001001",
    "101011101110111111011101101001",
    "100000001000033000010000000001",
    "101111101011111111010111111101",
    "100000000000000000000000000001",
    "111111111111111111111111111111"
]

class Oyun:
    def __init__(self):
        pygame.init()
        self.ekran = pygame.display.set_mode((GENISLIK, YUKSEKLIK))
        pygame.display.set_caption("Minimal Pac-Man")
        self.saat = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.reset()

    def reset(self):
        self.duvarlar = []
        self.yemler = []
        self.hayaletler = []
        self.oyuncu = None
        self.skor = 0
        self.oyun_bitti = False
        self.kazandi = False

        # Haritayı oku ve nesneleri oluştur
        for y, satir in enumerate(HARITA):
            for x, char in enumerate(satir):
                rect = pygame.Rect(x * BLOCK_BOYUT, y * BLOCK_BOYUT, BLOCK_BOYUT, BLOCK_BOYUT)
                if char == "1":
                    self.duvarlar.append(rect)
                elif char == "0" or char == "2" or char == "3":
                    self.yemler.append(rect) # Pacman ve hayalet altinda da yem olsun
                
                if char == "2":
                    self.oyuncu = pygame.Rect(x * BLOCK_BOYUT, y * BLOCK_BOYUT, BLOCK_BOYUT - 2, BLOCK_BOYUT - 2)
                elif char == "3":
                    # [rect, hiz_x, hiz_y]
                    self.hayaletler.append([rect, HIZ//2, 0]) 

    def hareket_ettir(self, rect, dx, dy):
        # Gelecekteki konumu test et
        rect.x += dx
        rect.y += dy
        
        # Duvarlara çarpıyor mu?
        for duvar in self.duvarlar:
            if rect.colliderect(duvar):
                rect.x -= dx # Geri al
                rect.y -= dy
                return False # Hareket başarısız
        return True # Hareket başarılı

    def run(self):
        dx, dy = 0, 0
        while True:
            self.ekran.fill(SIYAH)
            
            # Olayları Dinle
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and not self.oyun_bitti:
                    if event.key == pygame.K_LEFT:  dx, dy = -HIZ, 0
                    elif event.key == pygame.K_RIGHT: dx, dy = HIZ, 0
                    elif event.key == pygame.K_UP:    dx, dy = 0, -HIZ
                    elif event.key == pygame.K_DOWN:  dx, dy = 0, HIZ
                if event.type == pygame.KEYDOWN and self.oyun_bitti:
                    self.reset() # R tuşu veya herhangi bir tuşla restart

            if not self.oyun_bitti:
                # Oyuncu Hareketi
                self.hareket_ettir(self.oyuncu, dx, dy)

                # Yem Yeme
                for yem in self.yemler[:]:
                    if self.oyuncu.colliderect(yem):
                        self.yemler.remove(yem)
                        self.skor += 10

                # Kazanma Kontrolü
                if not self.yemler:
                    self.oyun_bitti = True; self.kazandi = True

                # Hayalet Yapay Zekası (Basit Rastgele Gezme)
                for h in self.hayaletler:
                    h_rect, hx, hy = h[0], h[1], h[2]
                    if not self.hareket_ettir(h_rect, hx, hy): # Duvara çarparsa yön değiştir
                        yonler = [(HIZ//2, 0), (-HIZ//2, 0), (0, HIZ//2), (0, -HIZ//2)]
                        h[1], h[2] = random.choice(yonler)
                    
                    # Çarpışma Kontrolü
                    if self.oyuncu.colliderect(h_rect):
                        self.oyun_bitti = True; self.kazandi = False

            # --- ÇİZİMLER ---
            for d in self.duvarlar: pygame.draw.rect(self.ekran, MAVI, d)
            for y in self.yemler:   pygame.draw.circle(self.ekran, BEYAZ, (y.centerx, y.centery), 3)
            for h in self.hayaletler: pygame.draw.rect(self.ekran, KIRMIZI, h[0])
            pygame.draw.circle(self.ekran, SARI, self.oyuncu.center, BLOCK_BOYUT // 2)

            # UI
            skor_text = self.font.render(f"Skor: {self.skor}", True, BEYAZ)
            self.ekran.blit(skor_text, (5, 5))

            if self.oyun_bitti:
                sonuc = "KAZANDIN!" if self.kazandi else "KAYBETTIN!"
                son_text = self.font.render(f"{sonuc} (Yeniden baslamak icin bir tusa bas)", True, SARI)
                self.ekran.blit(son_text, (GENISLIK//2 - 150, YUKSEKLIK//2))

            pygame.display.flip()
            self.saat.tick(30)

if __name__ == "__main__":
    Oyun().run()