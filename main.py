"""Entry point: python main.py"""
import sys

from PyQt6.QtWidgets import QApplication

from storage import AuthService, ClinicData
from styles import STYLESHEET
from ui import LoginWindow, MainWindow


class Controller:
    def __init__(self):
        self.clinic = ClinicData()
        self.auth = AuthService()
        self.login = self.main = None

    def show_login(self):
        self.login = LoginWindow(self.auth)
        self.login.logged_in.connect(self.show_main)
        self.login.show()
        if self.main:
            self.main.close()
            self.main = None

    def show_main(self, username, role):
        self.main = MainWindow(self.clinic, username, role)
        self.main.logout_requested.connect(self.show_login)
        self.main.show()
        self.login.close()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    controller = Controller()
    controller.show_login()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
