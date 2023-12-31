from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.uic import loadUi
from autoSMS import autoSMSSerial
import module
import sys


class Main(QMainWindow):

    path = module.Path(__file__)
    version = "1.0"
    app_tile = "Auto SMS Setup"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(self.path.source.join("ui", "main.ui"), self)
        self.setWindowTitle(self.app_tile + " - Version " + self.version)

        self.pb_phone.hide()
        self.pb_sms.hide()

        self.btn_connect.clicked.connect(self._on_connect_clicked)
        self.btn_read_phone.clicked.connect(self._on_read_phone_clicked)
        self.btn_write_phone.clicked.connect(self._on_write_phone_clicked)
        self.btn_read_sms.clicked.connect(self._on_read_sms_clicked)
        self.btn_write_sms.clicked.connect(self._on_write_sms_clicked)
        self.plain_content.textChanged.connect(lambda: self.lb_count.setText(str(len(self.plain_content.toPlainText()))))

        self._thread = None
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
    
    def try_connect(self, port=None):
        try:
            self.setup = autoSMSSerial(port)
            self.cbb_port.setCurrentText(self.setup.Serial.port)
            self.show_connected()
        except Exception as e:
            self.show_disconnected()
            return str(e)
        return ""

    def get_bytes_input(self) -> bytes:
        bit0 = 1 if self.cb_bit0.checkState() else 0
        bit1 = 1 if self.cb_bit1.checkState() else 0
        bit2 = 1 if self.cb_bit2.checkState() else 0
        bit3 = 1 if self.cb_bit3.checkState() else 0
        bit4 = 1 if self.cb_bit4.checkState() else 0
        return (bit0 + bit1*2 + bit2*4 + bit3*8 + bit4*16).to_bytes()
    
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
        if error := self.try_connect(self.cbb_port.currentText()):
            QMessageBox.warning(None, "Connection Failed", error)
        self.timer.start(500)
    
    def _on_read_phone_clicked(self):
        if not self.setup:
            if error := self.try_connect():
                return QMessageBox.warning(None, "Connection Failed", error)
        self._thread = Worker(self.setup.read_phone_number, [])
        self._thread.error.connect(self._on_process_error)
        self._thread.update_percentage.connect(self._on_update_percentage)
        self._thread.success.connect(self._read_phone_success)
        self._start_process()
        self._thread.start()
    
    def _read_phone_success(self, phone):
        self.cbb_phone.setCurrentText(phone[0:3])
        self.line_phone.setText(phone[3:])
        self._stop_process()

    def _on_write_phone_clicked(self):
        if not self.setup:
            if error := self.try_connect():
                return QMessageBox.warning(None, "Connection Failed", error)
        phone = self.line_phone.text()
        if not phone.isdecimal():
            return QMessageBox.warning(None, self.app_tile, "Phone number invalid, must be is decimal")
        self._thread = Worker(self.setup.write_phone_number, [self.cbb_phone.currentText() + phone])
        self._thread.error.connect(self._on_process_error)
        self._thread.update_percentage.connect(self._on_update_percentage)
        self._thread.success.connect(self._stop_process)
        self._start_process()
        self._thread.start()
        
    def _on_read_sms_clicked(self):
        if not self.setup:
            if error := self.try_connect():
                return QMessageBox.warning(None, "Connection Failed", error)
        sms_code = self.get_bytes_input()
        if sms_code == b'\x00':
            return QMessageBox.warning(None, self.app_tile, "Input must be different 0-0-0-0-0")
        self._thread = Worker(self.setup.read_SMS, [sms_code])
        self._thread.error.connect(self._on_process_error)
        self._thread.update_percentage.connect(self._on_update_percentage)
        self._thread.success.connect(self._read_sms_success)
        self._start_process()
        self._thread.start()
    
    def _read_sms_success(self, sms):
        self.plain_content.setPlainText(sms)
        self._stop_process()
    
    def _on_write_sms_clicked(self):
        if not self.setup:
            if error := self.try_connect():
                return QMessageBox.warning(None, "Connection Failed", error)
        sms_code = self.get_bytes_input()
        if sms_code == b'\x00':
            return QMessageBox.warning(None, self.app_tile, "Input must be different 0-0-0-0-0")
        self._thread = Worker(self.setup.write_SMS, [sms_code, self.plain_content.toPlainText()])
        self._thread.error.connect(self._on_process_error)
        self._thread.update_percentage.connect(self._on_update_percentage)
        self._thread.success.connect(self._stop_process)
        self._start_process()
        self._thread.start()

    def _start_process(self):
        self.btn_write_phone.hide()
        self.btn_read_phone.hide()
        self.btn_write_sms.hide()
        self.btn_read_sms.hide()
        self.pb_phone.show()
        self.pb_sms.show()
        self.pb_phone.setValue(0)
        self.pb_sms.setValue(0)

    def _stop_process(self, *args, **kwargs):
        self.btn_write_phone.show()
        self.btn_read_phone.show()
        self.btn_write_sms.show()
        self.btn_read_sms.show()
        self.pb_phone.hide()
        self.pb_sms.hide()
    
    def _on_process_error(self, error):
        self.tabWidget.setStyleSheet("QProgressBar {border: 1px solid white;border-radius: 3px;text-align: center;background-color: white;color: black;} QProgressBar::chunk {background-color: red;}")
        QMessageBox.critical(None, "Write phone number error", error)
        self._stop_process()
        self.tabWidget.setStyleSheet("QProgressBar {border: 1px solid white;border-radius: 3px;text-align: center;background-color: white;color: black;} QProgressBar::chunk {background-color: green;}")
    
    def _on_update_percentage(self, percen):
        self.pb_phone.setValue(percen)
        self.pb_sms.setValue(percen)
    
    def closeEvent(self, e):
        if self._thread and self._thread.isRunning():
            btn = QMessageBox.warning(None, self.app_tile, "Data is being transmitted! Are you sure to exit?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if btn == QMessageBox.StandardButton.Yes:
                self._thread.terminate()
                self.setup.Serial.close()
                e.accept()
            else:
                e.ignore()
        else:
            if self.setup:
                self.setup.Serial.close()
            e.accept()


class Worker(QThread):
    update_percentage = pyqtSignal(int)
    error = pyqtSignal(str)
    success = pyqtSignal(str)

    def __init__(self, method, arg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.method = method
        self.arg = arg

    def run(self):
        try:
            method = self.method(*self.arg)
            while True:
                percen = next(method)
                self.update_percentage.emit(percen)
        except StopIteration as _return:
            self.success.emit(_return.value)
        except Exception as e:
            self.error.emit(str(e))


if __name__ == "__main__":
    module.alert_excepthook()
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
