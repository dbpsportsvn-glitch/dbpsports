#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django với database đúng
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
os.environ.setdefault('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
os.environ.setdefault('FACEBOOK_APP_ID', 'test')
os.environ.setdefault('FACEBOOK_APP_SECRET', 'test')
os.environ.setdefault('FACEBOOK_SECRET_KEY', 'test')
os.environ.setdefault('GOOGLE_OAUTH2_CLIENT_ID', 'test')
os.environ.setdefault('GOOGLE_OAUTH2_CLIENT_SECRET', 'test')

django.setup()

from shop.models import Order
from shop.tasks import send_order_confirmation_email, send_order_notification_admin_email

def test_customer_email():
    """Test email gửi cho khách hàng với fix mới"""
    
    print("=" * 60)
    print("TEST EMAIL KHÁCH HÀNG - SAU KHI FIX")
    print("=" * 60)
    
    # Get latest order
    latest_order = Order.objects.order_by('-created_at').first()
    
    if not latest_order:
        print("❌ Không tìm thấy đơn hàng nào")
        print("\nVui lòng:")
        print("1. Đặt một đơn hàng test trên website")
        print("2. Hoặc kiểm tra xem database có đơn hàng không")
        return
    
    print(f"\n📦 Đơn hàng: {latest_order.order_number}")
    print(f"👤 Khách hàng: {latest_order.customer_name}")
    print(f"📧 Email: {latest_order.customer_email}")
    print(f"💰 Tổng tiền: {latest_order.total_amount:,.0f}đ")
    print(f"📅 Ngày đặt: {latest_order.created_at.strftime('%d/%m/%Y %H:%M')}")
    
    print("\n" + "-" * 60)
    print("🔄 Đang gửi email xác nhận cho khách hàng...")
    print("-" * 60)
    
    try:
        # Gửi email cho khách hàng với fix mới
        send_order_confirmation_email(latest_order.id)
        print("\n✅ ĐÃ GỬI EMAIL CHO KHÁCH HÀNG THÀNH CÔNG!")
        print(f"   → Gửi đến: {latest_order.customer_email}")
        print("\n💡 Kiểm tra:")
        print("   1. Hộp thư đến của khách hàng")
        print("   2. Thư mục Spam/Junk nếu không thấy")
        print("   3. Email sẽ có cả plain text và HTML content")
    except Exception as e:
        print(f"\n❌ LỖI KHI GỬI EMAIL: {str(e)}")
        print("\n🔍 Debug info:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_customer_email()

