#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
    """Test email xac nhan don hang cho khach hang"""
    
    # Mock data cho don hang
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

def main():
    """Chạy test email"""
    print("Bat dau test render email voi template moi...")
    print("Email se duoc hien thi trong console")
    print("-" * 60)
    
    print("\nDang test: Email xac nhan don hang Shop")
    if test_shop_customer_email():
        print("SUCCESS!")
    else:
        print("FAILED!")
    
    print("\nHoan thanh test!")

if __name__ == '__main__':
    main()
