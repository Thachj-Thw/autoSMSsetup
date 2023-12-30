import serial
from time import sleep
import serial.tools.list_ports

class autoSMSSerial:
    
    WRITE_SMS   = b'\x02'
    WRITE_PHONE = b'\x03'
    READ_SMS    = b'\x04'
    READ_PHONE  = b'\x05'

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
            self.Serial = serial.Serial(port, 9600)
            self.Serial.write(b'\x01')
            self.Serial.timeout = 1
            if self.Serial.read(1) != b'\x00':
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
                    ser = serial.Serial(port, 9600)
                except:
                    continue
                ser.write(b'\x01')
                ser.timeout = 1
                if ser.read(1) == b'\x00':
                    return ser
                ser.close()
    
    def read_SMS(self, sms_code: bytes) -> str:
        self.Serial.write(self.READ_SMS)
        self.Serial.write(sms_code)
        if self.Serial.read(1) == b'\x01':        # waitting for start
            raise Exception(f"code: {sms_code}")
        sms = ""
        i = 0
        char = self.Serial.read(1)
        while char != b'\x1A':
            sms += char.decode()
            yield int(i)
            i += .39
            char = self.Serial.read(1)
        yield 100
        return sms

    def write_SMS(self, sms_code: bytes, sms: str) -> None:
        self.Serial.write(self.WRITE_SMS)
        self.Serial.write(sms_code)
        if self.Serial.read(1) == b'\x01':        # waitting for start
            raise Exception(f"code: {sms_code}\n{sms}")
        len_sms = len(sms)
        for i, b in enumerate(sms, start=1):
            self.Serial.write(b.encode())
            self.Serial.read(1)
            yield int((i / len_sms) * 100)
        self.Serial.write(b'\x1A')
        self.Serial.read(1)    # waitting for end
        sleep(.5)
    
    def read_phone_number(self) -> str:
        self.Serial.write(self.READ_PHONE)
        phone = ""
        i = 0
        if self.Serial.read(1) == b"\x01":
            raise Exception(f"code: {self.READ_PHONE}")
        while char != b'\x0D':
            phone += char.decode()
            yield int(i)
            i += .39
            char = self.Serial.read(1)
        yield 100
        return phone
    
    def write_phone_number(self, phone_number: str) -> str:
        self.Serial.write(self.WRITE_PHONE)
        if self.Serial.read(1) == b'\x01':        # waitting for start
            raise Exception(f"phone number: {phone_number}")
        len_pn = len(phone_number)
        for i, b in enumerate(phone_number, start=1):
            self.Serial.write(b.encode())
            self.Serial.read(1)
            yield int((i / len_pn) * 100)
        self.Serial.write(b'\x0D')
        self.Serial.read(1)    # waitting for end
        sleep(.5)
 