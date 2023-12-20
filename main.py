import serial
from time import sleep

import serial.tools.list_ports
ports = serial.tools.list_ports.comports()


class autoSMSSerial:

    def __init__(self):
        self.ports = serial.tools.list_ports.comports()
        self.Serial = self.auto_connect()
        if not self.Serial:
            raise Exception("Device not found")
    
    def auto_connect(self) -> serial.Serial | None:
        for port, desc, _ in sorted(self.ports):
            print(port, desc)
            if "CH340" in desc:
                ser = serial.Serial(port, 9600)
                ser.write(b'\x01')
                ser.timeout = 3
                if ser.read(1) == b'\x00':
                    return ser

    def write_SMS(self, sms_code: bytes, sms: str) -> None:
        self.Serial.write(b'\x02')
        self.Serial.write(sms_code)
        if self.Serial.read(1) == b'\x01':        # waitting for start
            raise Exception(f"Write SMS Error code: {sms_code}\n{sms}")
        len_sms = len(sms)
        for i, st in enumerate(sms):
            self.Serial.write(st.encode())
            self.Serial.read()
            yield int((i / len_sms) * 100)
        self.Serial.write(b'\x1A')
        self.Serial.read()    # waitting for end
        sleep(.5)
    
    def write_phone_number(self, phone_number: str) -> None:
        self.Serial.write(b'\x03')
        if self.Serial.read(1) == b'\x01':        # waitting for start
            raise Exception(f"Write Phone Number Error:\n{phone_number}")
        len_pn = len(phone_number)
        for i, st in enumerate(phone_number):
            self.Serial.write(st.encode())
            self.Serial.read()
            yield int((i / len_pn) * 100)
        self.Serial.write(b'\x0D')
        self.Serial.read()    # waitting for end
        sleep(.5)
