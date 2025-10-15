#!/usr/bin/env python3
"""
Script test đơn giản để hiển thị email template trong console
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
os.environ.setdefault('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

django.setup()

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

def test_shop_customer_email():
    """Test email xác nhận đơn hàng cho khách hàng"""
    
    # Mock data cho đơn hàng
    order_data = {
        'order': {
            'order_number': 'DBP2025001',
            'customer_name': 'Nguyen Van A',
            'customer_email': 'thienhamedia2024@gmail.com',
            'customer_phone': '0123456789',
            'created_at': timezone.now(),
            'get_status_display': 'Dang xu ly',
            'get_payment_method_display': 'Chuyen khoan',
            'shipping_address': '123 Duong ABC',
            'shipping_district': 'Quan 1',
            'shipping_city': 'TP.HCM',
            'shipping_fee': 30000,
            'total_amount': 450000,
            'subtotal': 420000,
            'items': [
                {
                    'product': {'name': 'Giay bong da Nike'},
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
            subject='Xac nhan don hang #DBP2025001 - DBP Sports',
            message='',
            from_email='DBP Sports <noreply@dbpsports.com>',
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("SUCCESS: Da render email xac nhan don hang!")
        return True
    except Exception as e:
        print(f"ERROR: Loi render email: {e}")
        return False

def test_tournament_announcement():
    """Test email thông báo giải đấu"""
    
    # Mock data cho thông báo
    announcement_data = {
        'announcement': {
            'title': 'Thong bao quan trong ve lich thi dau',
            'content': 'Kinh gui cac doi truong,\n\nBan to chuc xin thong bao lich thi dau vong loai se duoc cap nhat vao ngay mai.\n\nVui long theo doi website de cap nhat thong tin moi nhat.\n\nTran trong.',
            'tournament': {'name': 'Giai bong da phong trao 2025'},
            'created_at': timezone.now()
        }
    }
    
    # Render template
    html_message = render_to_string('tournaments/emails/announcement_notification.html', announcement_data)
    
    # Gửi email
    try:
        send_mail(
            subject='Thong bao moi tu giai Giai bong da phong trao 2025 - DBP Sports',
            message='',
            from_email='DBP Sports <noreply@dbpsports.com>',
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("SUCCESS: Da render email thong bao giai dau!")
        return True
    except Exception as e:
        print(f"ERROR: Loi render email: {e}")
        return False

def test_payment_confirmed():
    """Test email xác nhận thanh toán"""
    
    # Mock data cho đội bóng
    team_data = {
        'team': {
            'name': 'Doi bong ABC',
            'tournament': {
                'name': 'Giai bong da phong trao 2025',
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
            subject='Xac nhan thanh toan thanh cong - Giai bong da phong trao 2025 - DBP Sports',
            message='',
            from_email='DBP Sports <noreply@dbpsports.com>',
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("SUCCESS: Da render email xac nhan thanh toan!")
        return True
    except Exception as e:
        print(f"ERROR: Loi render email: {e}")
        return False

def test_organization_approved():
    """Test email đơn vị được duyệt"""
    
    # Mock data cho đơn vị
    org_data = {
        'organization': {
            'name': 'CLB The thao ABC',
            'approved_at': timezone.now()
        },
        'owner': {
            'get_full_name': 'Nguyen Van B',
            'username': 'nguyenvanb',
            'email': 'thienhamedia2024@gmail.com'
        }
    }
    
    # Render template
    html_message = render_to_string('organizations/emails/organization_approved.html', org_data)
    
    # Gửi email
    try:
        send_mail(
            subject='Don vi to chuc da duoc duyet - DBP Sports',
            message='',
            from_email='DBP Sports <noreply@dbpsports.com>',
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("SUCCESS: Da render email don vi duoc duyet!")
        return True
    except Exception as e:
        print(f"ERROR: Loi render email: {e}")
        return False

def main():
    """Chạy tất cả test email"""
    print("Bat dau test render email voi template moi...")
    print("Email se duoc hien thi trong console")
    print("-" * 60)
    
    # Test các loại email
    tests = [
        ("Email xac nhan don hang Shop", test_shop_customer_email),
        ("Email thong bao giai dau", test_tournament_announcement),
        ("Email xac nhan thanh toan", test_payment_confirmed),
        ("Email don vi duoc duyet", test_organization_approved),
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nDang test: {test_name}")
        if test_func():
            success_count += 1
        print("-" * 40)
    
    print(f"\nKet qua: {success_count}/{total_count} email duoc render thanh cong")
    
    if success_count == total_count:
        print("Tat ca email da duoc render thanh cong!")
        print("Cac email da duoc hien thi trong console phia tren")
    else:
        print("Mot so email gap loi, vui long kiem tra template")

if __name__ == '__main__':
    main()
