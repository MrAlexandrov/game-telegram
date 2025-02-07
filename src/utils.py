import os
import qrcode

def generate_qr_code(data):
    # Задаём путь к файлу
    directory = "qr"
    filename = os.path.join(directory, "link.jpeg")
    
    # Создаём папку, если она не существует
    os.makedirs(directory, exist_ok=True)
    
    # Генерация QR-кода
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename, format="JPEG")
    
    return filename

import re

def is_valid_uuid4(s):
    uuid4_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid4_pattern.match(s))
