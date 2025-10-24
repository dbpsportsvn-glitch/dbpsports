#!/usr/bin/env python
"""
Script đơn giản để gửi newsletter
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from dbpsports_core.views import send_newsletter_bulk

def send_tournament_newsletter():
    """Gửi newsletter về giải đấu mới"""
    
    subject = "Giai bong da phong trao thang 12 sap khoi tranh!"
    
    content = """
    <h2>Thong bao giai dau moi!</h2>
    <p>Chao mung ban den voi giai bong da phong trao thang 12!</p>
    
    <h3>Thoi gian:</h3>
    <p>15/12/2024 - 31/12/2024</p>
    
    <h3>Dia diem:</h3>
    <p>San van dong Dien Bien</p>
    
    <h3>Giai thuong:</h3>
    <ul>
        <li>Giai nhat: 5,000,000 VND</li>
        <li>Giai nhi: 3,000,000 VND</li>
        <li>Giai ba: 2,000,000 VND</li>
    </ul>
    
    <p>Hay dang ky ngay de tham gia!</p>
    <p>Cam on ban da dong hanh cung DBP Sports!</p>
    """
    
    print("[INFO] Dang gui newsletter giai dau...")
    result = send_newsletter_bulk(subject, content, test_mode=False)
    
    if result['success']:
        print(f"[SUCCESS] Thanh cong! Da gui {result['sent']}/{result['total']} email")
        if result['failed'] > 0:
            print(f"[WARNING] Co {result['failed']} email gui that bai")
    else:
        print(f"[ERROR] Loi: {result['error']}")

if __name__ == "__main__":
    send_tournament_newsletter()
