#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để gửi email thật với template mới
Cần cấu hình SMTP trong file .env
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')

django.setup()

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

def send_shop_customer_email():
    """Gửi email xác nhận đơn hàng cho khách hàng"""
    
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
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("SUCCESS: Da gui email xac nhan don hang!")
        return True
    except Exception as e:
        print(f"ERROR: Loi gui email: {e}")
        return False

def send_tournament_announcement():
    """Gửi email thông báo giải đấu"""
    
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
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("SUCCESS: Da gui email thong bao giai dau!")
        return True
    except Exception as e:
        print(f"ERROR: Loi gui email: {e}")
        return False

def send_payment_confirmed():
    """Gửi email xác nhận thanh toán"""
    
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
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("SUCCESS: Da gui email xac nhan thanh toan!")
        return True
    except Exception as e:
        print(f"ERROR: Loi gui email: {e}")
        return False

def send_organization_approved():
    """Gửi email đơn vị được duyệt"""
    
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
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['thienhamedia2024@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        print("SUCCESS: Da gui email don vi duoc duyet!")
        return True
    except Exception as e:
        print(f"ERROR: Loi gui email: {e}")
        return False

def main():
    """Gửi tất cả email"""
    print("Bat dau gui email voi template moi...")
    print("Dia chi nhan: thienhamedia2024@gmail.com")
    print("-" * 60)
    
    # Kiểm tra cấu hình email
    if not settings.EMAIL_HOST_USER:
        print("ERROR: Chua cau hinh EMAIL_HOST_USER trong file .env")
        print("Vui long tao file .env va cau hinh SMTP")
        return
    
    # Gửi các email
    tests = [
        ("Email xac nhan don hang Shop", send_shop_customer_email),
        ("Email thong bao giai dau", send_tournament_announcement),
        ("Email xac nhan thanh toan", send_payment_confirmed),
        ("Email don vi duoc duyet", send_organization_approved),
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nDang gui: {test_name}")
        if test_func():
            success_count += 1
        print("-" * 40)
    
    print(f"\nKet qua: {success_count}/{total_count} email duoc gui thanh cong")
    
    if success_count == total_count:
        print("Tat ca email da duoc gui thanh cong!")
        print("Vui long kiem tra hop thu thienhamedia2024@gmail.com")
    else:
        print("Mot so email gap loi, vui long kiem tra cau hinh SMTP")

if __name__ == '__main__':
    main()
