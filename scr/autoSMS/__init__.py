import serial
from time import sleep
import serial.tools.list_ports

class autoSMSSerial:
    
    OK          = b'\x00'
    ERROR       = b'\x01'
    PING        = b'\x01'
    WRITE_SMS   = b'\x02'
    WRITE_PHONE = b'\x03'
    READ_SMS    = b'\x04'
    READ_PHONE  = b'\x05'
    END_SMS     = b'\x1A'
    END_PHONE   = b'\x0D'
    BAUDRATE   = 115200

    @staticmethod
    def get_ports() -> list:
        return serial.tools.list_ports.comports()
    
    @staticmethod
    def get_ports_name() -> list:
        ports = []
        for port, _, _ in autoSMSSerial.get_ports():
            ports.append(port)
        return ports

    def __init__(self, port = None):
        self.ports = self.get_ports()
        if port:
            self.Serial = serial.Serial(port, self.BAUDRATE)
            self.Serial.write(self.PING)
            self.Serial.timeout = 1
            if self.Serial.read(1) != self.OK:
                self.Serial.close()
                raise Exception("Device is not responding")
        else:
            self.Serial = self.auto_connect()
            if not self.Serial:
                raise Exception("Can't find device, connect to device and try again")
            self.Serial.timeout = 1

    def auto_connect(self) -> serial.Serial | None:
        for port, desc, _ in sorted(self.ports):
            if "CH340" in desc:
                try:
                    ser = serial.Serial(port, self.BAUDRATE)
                except:
                    continue
                ser.write(self.PING)
                ser.timeout = 1
                if ser.read(1) == self.OK:
                    return ser
                ser.close()
    
    def read_SMS(self, sms_code: bytes) -> str:
        self._serial_write(self.READ_SMS, f"Invalid method code: {self.READ_SMS}")
        sms = b''
        i = 0
        self.Serial.write(sms_code)
        char = self.Serial.read(1)
        while char != self.END_SMS:
            sms += char
            yield int(i)
            i += .08
            char = self.Serial.read(1)
        yield 100
        self.Serial.read(1)
        return sms.decode('utf-16')

    def write_SMS(self, sms_code: bytes, sms: str) -> None:
        self._serial_write(self.WRITE_SMS, f"Invalid method code: {self.WRITE_SMS}")
        self._serial_write(sms_code)
        b_sms = sms.encode('utf-16')
        len_sms = len(b_sms)
        for i, b in enumerate(b_sms, start=1):
            self._serial_write(b.to_bytes(1))
            yield int((i / len_sms) * 100)
        self._serial_write(self.END_SMS)
        sleep(.5)
    
    def read_phone_number(self) -> str:
        self._serial_write(self.READ_PHONE, f"Invalid method code: {self.READ_PHONE}")
        phone = ""
        i = 0
        char = self.Serial.read(1)
        while char != self.END_PHONE:
            phone += char.decode()
            yield int(i)
            i += .08
            char = self.Serial.read(1)
        yield 100
        self.Serial.read(1)
        return phone
    
    def write_phone_number(self, phone_number: str) -> None:
        self._serial_write(self.WRITE_PHONE, f"Invalid method, code: {self.WRITE_PHONE}")
        len_pn = len(phone_number)
        for i, b in enumerate(phone_number, start=1):
            self._serial_write(b.encode())
            yield int((i / len_pn) * 100)
        self._serial_write(self.END_PHONE)
        sleep(.5)
    
    def _serial_write(self, byte: bytes, _exception: str = "Device can't read data. Check your connection"):
        self.Serial.write(byte)
        if self.Serial.read(1) == self.ERROR:
            raise Exception(_exception)

 