#!/usr/bin/env python3
"""
Script test để gửi email mẫu với template mới
"""

import os
import sys
import django
from django.conf import settings

# Thêm đường dẫn backend vào Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime

def test_shop_customer_email():
    """Test email xác nhận đơn hàng cho khách hàng"""
    
    # Mock data cho đơn hàng
    order_data = {
        'order': {
            'order_number': 'DBP2025001',
            'customer_name': 'Nguyễn Văn A',
            'customer_email': 'thienhamedia2024@gmail.com',
            'customer_phone': '0123456789',
            'created_at': timezone.now(),
            'get_status_display': 'Đang xử lý',
            'get_payment_method_display': 'Chuyển khoản',
            'shipping_address': '123 Đường ABC',
            'shipping_district': 'Quận 1',
            'shipping_city': 'TP.HCM',
            'shipping_fee': 30000,
            'total_amount': 450000,
            'subtotal': 420000,
            'items': [
                {
                    'product': {'name': 'Giày bóng đá Nike'},
                    'quantity': 1,
                    'price': 420000,
                    'total_price': 420000
                }
            ]
        }
    }
    
    # Render template
    html_message = render_to_string('shop/emails/customer_order_confirmation.html', order_data)
    
    # Gửi email
    try:
        send_mail(
            subject='✅ Xác nhận đơn hàng #DBP2025001 - DBP Sports',
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("✅ Đã gửi email xác nhận đơn hàng thành công!")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
        return False

def test_tournament_announcement():
    """Test email thông báo giải đấu"""
    
    # Mock data cho thông báo
    announcement_data = {
        'announcement': {
            'title': 'Thông báo quan trọng về lịch thi đấu',
            'content': 'Kính gửi các đội trưởng,\n\nBan tổ chức xin thông báo lịch thi đấu vòng loại sẽ được cập nhật vào ngày mai.\n\nVui lòng theo dõi website để cập nhật thông tin mới nhất.\n\nTrân trọng.',
            'tournament': {'name': 'Giải bóng đá phong trào 2025'},
            'created_at': timezone.now()
        }
    }
    
    # Render template
    html_message = render_to_string('tournaments/emails/announcement_notification.html', announcement_data)
    
    # Gửi email
    try:
        send_mail(
            subject='📢 Thông báo mới từ giải Giải bóng đá phong trào 2025 - DBP Sports',
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("✅ Đã gửi email thông báo giải đấu thành công!")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
        return False

def test_payment_confirmed():
    """Test email xác nhận thanh toán"""
    
    # Mock data cho đội bóng
    team_data = {
        'team': {
            'name': 'Đội bóng ABC',
            'tournament': {
                'name': 'Giải bóng đá phong trào 2025',
                'registration_fee': 500000
            },
            'payment_proof_uploaded_at': timezone.now()
        }
    }
    
    # Render template
    html_message = render_to_string('tournaments/emails/payment_confirmed.html', team_data)
    
    # Gửi email
    try:
        send_mail(
            subject='🎉 Xác nhận thanh toán thành công - Giải bóng đá phong trào 2025 - DBP Sports',
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("✅ Đã gửi email xác nhận thanh toán thành công!")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
        return False

def test_organization_approved():
    """Test email đơn vị được duyệt"""
    
    # Mock data cho đơn vị
    org_data = {
        'organization': {
            'name': 'CLB Thể thao ABC',
            'approved_at': timezone.now()
        },
        'owner': {
            'get_full_name': 'Nguyễn Văn B',
            'username': 'nguyenvanb',
            'email': 'thienhamedia2024@gmail.com'
        }
    }
    
    # Render template
    html_message = render_to_string('organizations/emails/organization_approved.html', org_data)
    
    # Gửi email
    try:
        send_mail(
            subject='🎉 Đơn vị tổ chức đã được duyệt - DBP Sports',
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("✅ Đã gửi email đơn vị được duyệt thành công!")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
        return False

def main():
    """Chạy tất cả test email"""
    print("🚀 Bắt đầu test gửi email với template mới...")
    print("📧 Địa chỉ nhận: thienhamedia2024@gmail.com")
    print("-" * 50)
    
    # Test các loại email
    tests = [
        ("Email xác nhận đơn hàng Shop", test_shop_customer_email),
        ("Email thông báo giải đấu", test_tournament_announcement),
        ("Email xác nhận thanh toán", test_payment_confirmed),
        ("Email đơn vị được duyệt", test_organization_approved),
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📤 Đang test: {test_name}")
        if test_func():
            success_count += 1
        print("-" * 30)
    
    print(f"\n📊 Kết quả: {success_count}/{total_count} email được gửi thành công")
    
    if success_count == total_count:
        print("🎉 Tất cả email đã được gửi thành công!")
        print("📧 Vui lòng kiểm tra hộp thư thienhamedia2024@gmail.com")
    else:
        print("⚠️ Một số email gặp lỗi, vui lòng kiểm tra cấu hình email")

if __name__ == '__main__':
    main()
