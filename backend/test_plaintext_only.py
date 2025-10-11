#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from shop.models import Order

def test_plaintext_only():
    """Test email chi co plain text, khong co HTML"""
    
    latest_order = Order.objects.order_by('-created_at').first()
    if not latest_order:
        print("No orders found")
        return
    
    print(f"=== Test Plain Text Only Email ===")
    print(f"Order: {latest_order.order_number}")
    print(f"Customer: {latest_order.customer_name}")
    print(f"Email: {latest_order.customer_email}")
    
    # Test 1: Email cuc ky don gian
    print("\n1. Testing ultra-simple email...")
    try:
        result = send_mail(
            'DBP Sports Order Confirmation',
            f'Hello {latest_order.customer_name}, your order {latest_order.order_number} has been confirmed. Total: {latest_order.total_amount:,.0f}d. Thank you!',
            settings.DEFAULT_FROM_EMAIL,
            [latest_order.customer_email],
            fail_silently=False,
        )
        print(f"[OK] Ultra-simple email sent: {result}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
    
    # Test 2: Email tieng Viet khong dau
    print("\n2. Testing Vietnamese without diacritics...")
    try:
        message = f"""
Xin chao {latest_order.customer_name},

Cam on ban da dat hang tai DBP Sports!

Ma don hang: {latest_order.order_number}
Tong tien: {latest_order.total_amount:,.0f}d

Chung toi se xu ly don hang som nhat.

Tran trong,
DBP Sports Team
        """
        result = send_mail(
            f'Xac nhan don hang {latest_order.order_number}',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [latest_order.customer_email],
            fail_silently=False,
        )
        print(f"[OK] Vietnamese email sent: {result}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
    
    # Test 3: Subject khac nhau
    print("\n3. Testing different subjects...")
    subjects = [
        'Your Order Confirmation',
        'DBP Sports - Thank You',
        f'Order {latest_order.order_number}',
        'Thank you for your order'
    ]
    
    for subject in subjects:
        try:
            result = send_mail(
                subject,
                f'Order {latest_order.order_number} confirmed. Total: {latest_order.total_amount:,.0f}d',
                settings.DEFAULT_FROM_EMAIL,
                [latest_order.customer_email],
                fail_silently=False,
            )
            print(f"[OK] Subject '{subject}': sent")
        except Exception as e:
            print(f"[ERROR] Subject '{subject}': {str(e)}")
    
    print("\n[INFO] Check your email inbox!")
    print("[INFO] If none of these arrive, the issue is NOT with content")
    print("[INFO] Possible causes: Gmail filtering all emails from this address")

if __name__ == "__main__":
    test_plaintext_only()
