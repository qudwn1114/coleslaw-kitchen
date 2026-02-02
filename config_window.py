from PyQt6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QRadioButton, QMessageBox
)
from config import save_config


class ConfigWindow(QDialog):
    def __init__(self, initial_config=None):
        super().__init__()
        self.setWindowTitle("Coleslaw POS Settings")
        self.setFixedSize(360, 280)

        layout = QVBoxLayout()

        # Server country
        layout.addWidget(QLabel("Server"))
        self.kr = QRadioButton("KR")
        self.jp = QRadioButton("JP")
        layout.addWidget(self.kr)
        layout.addWidget(self.jp)

        # 기존 값 초기화
        country = initial_config.get("country", "KR") if initial_config else "KR"
        if country.upper() == "JP":
            self.jp.setChecked(True)
        else:
            self.kr.setChecked(True)

        # Shop ID
        layout.addWidget(QLabel("Shop ID"))
        self.shop_id = QLineEdit()
        if initial_config:
            self.shop_id.setText(str(initial_config.get("shop_id", "")))
        layout.addWidget(self.shop_id)

        # Shop POS ID
        layout.addWidget(QLabel("Shop POS ID (shop_table_id)"))
        self.shop_table_id = QLineEdit()
        if initial_config:
            self.shop_table_id.setText(str(initial_config.get("shop_table_id", "")))
        layout.addWidget(self.shop_table_id)

        # Save 버튼
        btn = QPushButton("Save")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

        self.setLayout(layout)

    def save(self):
        try:
            config = {
                "country": "kr" if self.kr.isChecked() else "jp",
                "shop_id": int(self.shop_id.text()),
                "shop_table_id": int(self.shop_table_id.text())
            }
        except ValueError:
            QMessageBox.critical(self, "Error", "Number Only..")
            return

        save_config(config)
        self.accept()
