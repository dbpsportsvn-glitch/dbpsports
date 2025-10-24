#!/usr/bin/env python
"""
Script để gửi newsletter với nội dung tùy chỉnh
Cách sử dụng: python send_custom_newsletter.py
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
    
    subject = "🏆 Giải bóng đá phong trào tháng 12 sắp khởi tranh!"
    
    content = """
    <h2>🎉 Thông báo giải đấu mới!</h2>
    <p>Chào mừng bạn đến với giải bóng đá phong trào tháng 12!</p>
    
    <h3>📅 Thời gian:</h3>
    <p>15/12/2024 - 31/12/2024</p>
    
    <h3>📍 Địa điểm:</h3>
    <p>Sân vận động Điện Biên</p>
    
    <h3>🎁 Giải thưởng:</h3>
    <ul>
        <li>Giải nhất: 5,000,000 VNĐ</li>
        <li>Giải nhì: 3,000,000 VNĐ</li>
        <li>Giải ba: 2,000,000 VNĐ</li>
    </ul>
    
    <p>Hãy đăng ký ngay để tham gia!</p>
    <p>Cảm ơn bạn đã đồng hành cùng DBP Sports!</p>
    """
    
    print("[INFO] Dang gui newsletter...")
    result = send_newsletter_bulk(subject, content, test_mode=False)
    
    if result['success']:
        print(f"[SUCCESS] Thanh cong! Da gui {result['sent']}/{result['total']} email")
        if result['failed'] > 0:
            print(f"[WARNING] Co {result['failed']} email gui that bai")
    else:
        print(f"[ERROR] Loi: {result['error']}")

def send_shop_newsletter():
    """Gửi newsletter về shop"""
    
    subject = "🛒 Shop DBP Sports - Ưu đãi đặc biệt cuối năm!"
    
    content = """
    <h2>🎁 Ưu đãi đặc biệt cuối năm!</h2>
    <p>Shop DBP Sports có nhiều ưu đãi hấp dẫn cho bạn!</p>
    
    <h3>🔥 Flash Sale:</h3>
    <ul>
        <li>Giảm 50% tất cả áo đấu</li>
        <li>Giảm 30% giày thể thao</li>
        <li>Mua 2 tặng 1 phụ kiện</li>
    </ul>
    
    <h3>⏰ Thời gian:</h3>
    <p>1/12/2024 - 31/12/2024</p>
    
    <p>Hãy truy cập shop ngay để không bỏ lỡ!</p>
    """
    
    print("[INFO] Dang gui newsletter shop...")
    result = send_newsletter_bulk(subject, content, test_mode=False)
    
    if result['success']:
        print(f"[SUCCESS] Thanh cong! Da gui {result['sent']}/{result['total']} email")
    else:
        print(f"[ERROR] Loi: {result['error']}")

def send_test_newsletter():
    """Gửi newsletter test"""
    
    subject = "🧪 Newsletter Test - DBP Sports"
    
    content = """
    <h2>🧪 Đây là email test</h2>
    <p>Bạn đã nhận được email này để kiểm tra hệ thống newsletter.</p>
    <p>Cảm ơn bạn đã đăng ký nhận thông báo từ DBP Sports!</p>
    """
    
    print("[INFO] Dang gui newsletter test...")
    result = send_newsletter_bulk(subject, content, test_mode=True)
    
    if result['success']:
        print(f"[SUCCESS] Thanh cong! Da gui {result['sent']}/{result['total']} email")
    else:
        print(f"[ERROR] Loi: {result['error']}")

if __name__ == "__main__":
    print("[CHOICE] Chon loai newsletter muon gui:")
    print("1. Giai dau moi")
    print("2. Shop uu dai")
    print("3. Test")
    
    choice = input("Nhap lua chon (1-3): ").strip()
    
    if choice == "1":
        send_tournament_newsletter()
    elif choice == "2":
        send_shop_newsletter()
    elif choice == "3":
        send_test_newsletter()
    else:
        print("[ERROR] Lua chon khong hop le!")
