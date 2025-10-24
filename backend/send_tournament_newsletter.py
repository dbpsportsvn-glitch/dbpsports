#!/usr/bin/env python
"""
Script để gửi newsletter về giải đấu mới
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
    
    # CHỈNH SỬA TIÊU ĐỀ VÀ NỘI DUNG Ở ĐÂY:
    subject = "Giai bong da phong trao thang 12 - DBP Sports"
    
    content = """
    <h2>Chao mung ban den voi DBP Sports!</h2>
    <p>Chung toi co nhieu thong tin thu vi cho ban trong thang nay!</p>
    
    <h3>Giai dau sap dien ra:</h3>
    <p><strong>Giai bong da phong trao thang 12</strong></p>
    <ul>
        <li><strong>Thoi gian:</strong> 15/12/2024 - 31/12/2024</li>
        <li><strong>Dia diem:</strong> San van dong Dien Bien</li>
        <li><strong>Giai thuong:</strong> Tong gia tri 10,000,000 VND</li>
    </ul>
    
    <h3>Uu dai dac biet tu Shop:</h3>
    <ul>
        <li>Giam 30% tat ca ao dau</li>
        <li>Mua 2 tang 1 phu kien</li>
        <li>Free ship cho don hang tren 500,000 VND</li>
    </ul>
    
    <h3>Tin tuc noi bat:</h3>
    <p>Doi bong ABC vua gianh chien thang trong tran dau cuoi tuan!</p>
    
    <p><strong>Hay truy cap website de dang ky ngay!</strong></p>
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
