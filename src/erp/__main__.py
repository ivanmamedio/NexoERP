import sys

from PySide6.QtWidgets import QApplication, QMainWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("ERP")
    window.resize(1024, 720)
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
