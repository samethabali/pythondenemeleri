import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QHBoxLayout, QMessageBox, QDateEdit, QComboBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate


class PersistentTaskManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.task_file = "tasks.json"
        self.tasks = []
        self.initUI()
        self.load_tasks()

    def initUI(self):
        # Pencere Ayarları
        self.setWindowTitle("Görev Yönetim Uygulaması")
        self.setGeometry(200, 200, 600, 700)
        self.setStyleSheet("""
            QMainWindow { background-color: #2c3e50; }
            QLabel { color: #ecf0f1; font-size: 18px; }
            QLineEdit, QComboBox, QDateEdit, QListWidget {
                background-color: #ecf0f1; border-radius: 5px; font-size: 14px; padding: 5px;
            }
            QPushButton {
                background-color: #3498db; color: #ffffff; font-size: 14px; font-weight: bold;
                border-radius: 5px; padding: 10px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)

        # Ana Widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Başlık
        title = QLabel("Görev Yönetimi", self)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(title)

        # Görev Giriş Alanı
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Yeni görev girin...")
        layout.addWidget(self.input_field)

        # Kategori Seçimi
        self.category_selector = QComboBox(self)
        self.category_selector.addItems(["Genel", "İş", "Kişisel", "Alışveriş"])
        layout.addWidget(self.category_selector)

        # Tarih Seçimi
        self.date_picker = QDateEdit(self)
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        layout.addWidget(self.date_picker)

        # Görev Ekle Butonu
        add_button = QPushButton("Görev Ekle", self)
        add_button.clicked.connect(self.add_task)
        layout.addWidget(add_button)

        # Görev Listesi
        self.task_list = QListWidget(self)
        layout.addWidget(self.task_list)

        # Sil ve Temizle Butonları
        button_layout = QHBoxLayout()
        delete_button = QPushButton("Seçili Görevi Sil", self)
        delete_button.clicked.connect(self.delete_task)
        save_button = QPushButton("Görevleri Kaydet", self)
        save_button.clicked.connect(self.save_tasks)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)

    def add_task(self):
        task_text = self.input_field.text().strip()
        category = self.category_selector.currentText()
        date = self.date_picker.date().toString("yyyy-MM-dd")

        if task_text:
            task_entry = f"{task_text} | {category} | {date}"
            self.task_list.addItem(task_entry)
            self.tasks.append({"text": task_text, "category": category, "date": date})
            self.input_field.clear()
        else:
            QMessageBox.warning(self, "Uyarı", "Görev alanı boş bırakılamaz!")

    def delete_task(self):
        selected_item = self.task_list.currentItem()
        if selected_item:
            row = self.task_list.row(selected_item)
            self.task_list.takeItem(row)
            del self.tasks[row]
        else:
            QMessageBox.warning(self, "Uyarı", "Silmek için bir görev seçin!")

    def save_tasks(self):
        try:
            with open(self.task_file, "w") as file:
                json.dump(self.tasks, file, indent=4)
            QMessageBox.information(self, "Bilgi", "Görevler başarıyla kaydedildi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Görevler kaydedilirken bir hata oluştu: {e}")

    def load_tasks(self):
        try:
            with open(self.task_file, "r") as file:
                self.tasks = json.load(file)
                for task in self.tasks:
                    task_entry = f"{task['text']} | {task['category']} | {task['date']}"
                    self.task_list.addItem(task_entry)
        except FileNotFoundError:
            self.tasks = []  # Dosya bulunamazsa boş liste başlat
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Görevler yüklenirken bir hata oluştu: {e}")

# Uygulama Çalıştırma
if __name__ == "__main__":
    app = QApplication(sys.argv)
    task_manager = PersistentTaskManager()
    task_manager.show()
    sys.exit(app.exec_())
