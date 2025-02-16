import os
import qrcode

def generate_qr_code(data):
    # Задаём путь к файлу
    directory = "qr"
    filename = os.path.join(directory, "qr.jpeg")
    
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
