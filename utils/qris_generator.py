import qrcode
import io
import base64
from typing import Optional
from PIL import Image

def generate_qris_image(qris_string: str, logo_path: Optional[str] = None) -> bytes:
    """Generate gambar QRIS dari string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qris_string)
    qr.make(fit=True)
    
    # Buat gambar
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Tambah logo di tengah (opsional)
    if logo_path:
        try:
            logo = Image.open(logo_path)
            logo_size = min(img.size) // 4
            logo = logo.resize((logo_size, logo_size))
            
            pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
            img.paste(logo, pos, logo if logo.mode == 'RGBA' else None)
        except:
            pass
    
    # Convert ke bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer.getvalue()

def generate_qris_base64(qris_string: str) -> str:
    """Generate QRIS dalam format base64"""
    img_bytes = generate_qris_image(qris_string)
    return base64.b64encode(img_bytes).decode('utf-8')

def create_qris_string(amount: int, merchant_id: str = "SEBAR", merchant_name: str = "SEBAR BOT") -> str:
    """Buat string QRIS standar Indonesia (simplified)"""
    # Format QRIS standar (EMVCo)
    # Ini versi sederhana, untuk produksi gunakan library khusus
    
    qris_data = f"000201010212{len(merchant_id):02d}{merchant_id}5204000053033605802ID5913{merchant_name}6007JAKARTA610510316{len(str(amount)):02d}{amount}6304"
    
    # Tambah CRC16 (placeholder)
    crc = "0000"  # Seharusnya dihitung
    
    return qris_data + crc

def generate_payment_link(amount: int, order_id: str) -> str:
    """Generate link pembayaran (untuk QRIS dinamis)"""
    # Integrasi dengan payment gateway
    return f"https://payment.sebarbot.id/pay?amount={amount}&order={order_id}"
