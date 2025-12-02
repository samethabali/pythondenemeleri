import fitz  # PyMuPDF

# PDF'yi aç
doc = fitz.open("Samet_Can_Habali_CV.pdf")

# Mevcut meta verileri göster
print("Eski Meta Veriler:", doc.metadata)

# Yeni meta verileri belirle
doc.set_metadata({
    "title": "CV",
    "author": "Samet Can Habalı"
})

# Değişiklikleri kaydet
doc.save("duzenlenmis.pdf")
doc.close()

print("Meta veriler güncellendi!")
