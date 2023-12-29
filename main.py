from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QProgressBar
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.uic import loadUi
from autoSMS import autoSMSSerial
import module
import sys

class Main(QMainWindow):

    path = module.Path(__file__)
    version = "1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(self.path.source.join("ui", "main.ui"), self)
        self.setWindowTitle("Auto SMS Setup - Version " + self.version)

        self.pb_phone.hide()
        self.pb_sms.hide()

        self.btn_connect.clicked.connect(self._on_connect_clicked)
        self.btn_read_phone.clicked.connect(self._on_read_phone_clicked)
        self.btn_write_phone.clicked.connect(self._on_write_phone_clicked)
        self.btn_read_sms.clicked.connect(self._on_read_sms_clicked)
        self.btn_write_sms.clicked.connect(self._on_write_sms_clicked)

        self.ports = set(autoSMSSerial.get_ports_name())
        self.cbb_port.addItems(self.ports)
        self.timer = QTimer()
        self.timer.timeout.connect(self._usb_monitor)
        self.timer.start(500)
        self.show()
        self.setup = None
        while not self.setup:
            if error := self.try_connect():
                btn = QMessageBox.information(None, "Connection Failed", error, 
                                            QMessageBox.StandardButton.Retry|QMessageBox.StandardButton.Ignore|QMessageBox.StandardButton.Close)
                if btn == QMessageBox.StandardButton.Close:
                    sys.exit(0)
                elif btn == QMessageBox.StandardButton.Ignore:
                    break
        
    def show_disconnected(self):
        self.lb_status.setText("Disconnected")
        self.lb_status.setStyleSheet("color: red;")
    
    def show_connected(self):
        self.lb_status.setText("Connected")
        self.lb_status.setStyleSheet("color: green;")
    
    def try_connect(self):
        try:
            self.setup = autoSMSSerial()
            self.cbb_port.setCurrentText(self.setup.Serial.port)
            self.show_connected()
        except Exception as e:
            self.show_disconnected()
            return str(e)
        return ""
    
    def _usb_monitor(self):
        if self.setup:
            ports = set(autoSMSSerial.get_ports_name())
            if ports.symmetric_difference(self.ports):
                self.ports = ports
                self.cbb_port.clear()
                self.cbb_port.addItems(self.ports)
                if self.setup.Serial.port in self.ports:
                    self.cbb_port.setCurrentText(self.setup.Serial.port)
                else:
                    self.setup = None
                    self.show_disconnected()
        else:
            self.try_connect()

    def _on_connect_clicked(self):
        self.timer.stop()
        if self.setup:
            self.setup.Serial.close()
            self.setup = None
            self.show_disconnected()
        if error := self.try_connect():
            QMessageBox.warning(None, "Connection Failed", error)
        self.timer.start(500)
    
    def _on_read_phone_clicked(self):
        if not self.setup:
            if error := self.try_connect():
                return QMessageBox.warning(None, "Connection Failed", error)
        try:
            phone = self.setup.read_phone_number()
            self.cbb_phone.setCurrentText(phone[0:3])
            self.line_phone.setText(phone[3:])
        except Exception as e:
                QMessageBox.critical(None, "Read phone number error", str(e))

    def _on_write_phone_clicked(self):
        if not self.setup:
            if error := self.try_connect():
                return QMessageBox.warning(None, "Connection Failed", error)
        # try:
        self.thread = Worker(self.setup.write_phone_number, [self.cbb_phone.currentText() + self.line_phone.text()])
        self.thread.error.connect(self._on_process_error)
        self.thread.update_percentage.connect(self._on_update_percentage)
        self.thread.success.connect(self._on_process_success)
        self._on_start_process()
        self.thread.start()

    def _on_start_process(self):
        self.tabWidget.setStyleSheet("QProgressBar {border: 1px solid white;border-radius: 3px;text-align: center;background-color: white;color: black;} QProgressBar::chunk {background-color: green;}")
        self.btn_write_phone.hide()
        self.btn_read_phone.hide()
        self.btn_write_sms.hide()
        self.btn_read_sms.hide()
        self.pb_phone.show()
        self.pb_sms.show()
        self.pb_phone.setValue(0)
        self.pb_sms.setValue(0)

    def _on_process_success(self):
        self.btn_write_phone.show()
        self.btn_read_phone.show()
        self.btn_write_sms.show()
        self.btn_read_sms.show()
        self.pb_phone.hide()
        self.pb_sms.hide()
    
    def _on_process_error(self, error):
        self.tabWidget.setStyleSheet("QProgressBar {border: 1px solid white;border-radius: 3px;text-align: center;background-color: white;color: black;} QProgressBar::chunk {background-color: red;}")
        QMessageBox.critical(None, "Write phone number error", error)
        self._on_process_success()
    
    def _on_update_percentage(self, percen):
        self.pb_phone.setValue(percen)
        self.pb_sms.setValue(percen)
        
    def _on_read_sms_clicked(self):
        if not self.setup:
            if error := self.try_connect():
                return QMessageBox.warning(None, "Connection Failed", error)
    
    def _on_write_sms_clicked(self):
        if not self.setup:
            if error := self.try_connect():
                return QMessageBox.warning(None, "Connection Failed", error)


class Worker(QThread):
    update_percentage = pyqtSignal(int)
    error = pyqtSignal(str)
    success = pyqtSignal()

    def __init__(self, method, arg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.method = method
        self.arg = arg

    def run(self):
        try:
            for percen in self.method(*self.arg):
                self.update_percentage.emit(percen)
        except Exception as e:
            self.error.emit(str(e))
        else:
            self.success.emit()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())