#!/usr/bin/env python
"""
Script để gửi newsletter về shop
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from dbpsports_core.views import send_newsletter_bulk

def send_shop_newsletter():
    """Gửi newsletter về shop"""
    
    subject = "Shop DBP Sports - Uu dai dac biet cuoi nam!"
    
    content = """
    <h2>Uu dai dac biet cuoi nam!</h2>
    <p>Shop DBP Sports co nhieu uu dai hap dan cho ban!</p>
    
    <h3>Flash Sale:</h3>
    <ul>
        <li>Giam 50% tat ca ao dau</li>
        <li>Giam 30% giay the thao</li>
        <li>Mua 2 tang 1 phu kien</li>
    </ul>
    
    <h3>Thoi gian:</h3>
    <p>1/12/2024 - 31/12/2024</p>
    
    <p>Hay truy cap shop ngay de khong bo lo!</p>
    <p>Cam on ban da dong hanh cung DBP Sports!</p>
    """
    
    print("[INFO] Dang gui newsletter shop...")
    result = send_newsletter_bulk(subject, content, test_mode=False)
    
    if result['success']:
        print(f"[SUCCESS] Thanh cong! Da gui {result['sent']}/{result['total']} email")
    else:
        print(f"[ERROR] Loi: {result['error']}")

if __name__ == "__main__":
    send_shop_newsletter()
