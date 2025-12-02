# database.py (Güncellenmiş Hali)
import sqlite3
import os

DB_FILE = "erp_sistemi.db"

def init_db():
    """ Veritabanını ve 'products' tablosunu oluşturur (eğer yoksa). """
    if os.path.exists(DB_FILE):
        print("Veritabanı zaten mevcut.")
        return # Zaten varsa tekrar oluşturma

    print("İlk kurulum: Veritabanı ve tablo oluşturuluyor...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE products (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL,
        stock INTEGER
    )
    """)
    # Test için birkaç örnek veri ekleyelim
    cursor.execute("INSERT INTO products VALUES ('URUN-001', 'Kola', 15.0, 100)")
    cursor.execute("INSERT INTO products VALUES ('URUN-002', 'Cips', 20.5, 50)")
    cursor.execute("INSERT INTO products VALUES ('URUN-003', 'Çikolata', 12.75, 75)")
    conn.commit()
    conn.close()
    print("Veritabanı hazır.")

def get_product(product_id):
    """
    SADECE ürün bilgilerini çeker. Hiçbir şeyi DEĞİŞTİRMEZ.
    (product_id, name, price, stock) tuple'ı veya None döner.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT product_id, name, price, stock FROM products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()
        return product
    except Exception as e:
        print(f"Veritabanı okuma hatası: {e}")
        return None
    finally:
        if conn:
            conn.close()

def modify_stock(product_id, amount):
    """
    Stoğu verilen 'amount' kadar artırır veya azaltır (örn: +10 veya -5).
    Stoğun eksiye düşmesini engeller.
    Başarılıysa True, başarısızsa (stok eksiye düşerse) False döner.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Stoğun (mevcut + değişiklik) >= 0 olmasını zorunlu kılan sorgu
        cursor.execute("""
            UPDATE products 
            SET stock = stock + ? 
            WHERE product_id = ? AND (stock + ?) >= 0
        """, (amount, product_id, amount))
        
        conn.commit()
        
        # Eğer rowcount 0 ise, ya ID yanlıştı ya da stok eksiye düşecekti.
        if cursor.rowcount > 0:
            print(f"Stok güncellendi: {product_id}, Değişim: {amount}")
            return True
        else:
            print(f"Stok güncelleme hatası (ID bulunamadı veya stok eksiye düşecekti): {product_id}")
            return False
            
    except Exception as e:
        print(f"Veritabanı yazma hatası: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_price(product_id, new_price):
    """
    Ürünün fiyatını günceller. Fiyatın 0'dan küçük olmasını engeller.
    """
    if new_price < 0:
        print("Fiyat 0'dan küçük olamaz.")
        return False
        
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET price = ? WHERE product_id = ?", (new_price, product_id))
        conn.commit()
        print(f"Fiyat güncellendi: {product_id}, Yeni Fiyat: {new_price}")
        return True
    except Exception as e:
        print(f"Veritabanı fiyat güncelleme hatası: {e}")
        return False
    finally:
        if conn:
            conn.close()