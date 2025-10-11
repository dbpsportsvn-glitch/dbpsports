#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from shop.models import Order
from shop.tasks import send_order_confirmation_email, send_order_notification_admin_email

def test_email_system():
    """Test email system với đơn hàng thực tế"""
    
    # Lấy đơn hàng gần nhất
    latest_order = Order.objects.order_by('-created_at').first()
    
    if not latest_order:
        print("Không có đơn hàng nào để test")
        return
    
    print(f"Testing email system with order: {latest_order.order_number}")
    print(f"Customer: {latest_order.customer_name} ({latest_order.customer_email})")
    
    # Test gửi email xác nhận cho khách hàng
    print("\n1. Testing customer confirmation email...")
    try:
        send_order_confirmation_email(latest_order.id)
        print("[OK] Customer confirmation email sent successfully!")
    except Exception as e:
        print(f"[ERROR] Error sending customer email: {str(e)}")
    
    # Test gửi email thông báo cho admin
    print("\n2. Testing admin notification email...")
    try:
        send_order_notification_admin_email(latest_order.id)
        print("[OK] Admin notification email sent successfully!")
    except Exception as e:
        print(f"[ERROR] Error sending admin email: {str(e)}")
    
    print("\n[INFO] Check your email inbox (or console output) for the test emails!")

if __name__ == "__main__":
    test_email_system()
