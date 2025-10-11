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

def test_official_emails():
    """Test email chính thức cho đơn hàng"""
    
    # Lấy đơn hàng mới nhất
    latest_order = Order.objects.order_by('-created_at').first()
    
    if not latest_order:
        print("Không có đơn hàng nào để test")
        return
    
    print(f"=== Testing Official Emails ===")
    print(f"Order: {latest_order.order_number}")
    print(f"Customer: {latest_order.customer_name}")
    print(f"Email: {latest_order.customer_email}")
    print(f"Payment Method: {latest_order.get_payment_method_display()}")
    print(f"Total: {latest_order.total_amount:,}đ")
    
    print(f"\n1. Testing Customer Confirmation Email...")
    try:
        send_order_confirmation_email(latest_order.id)
        print("[OK] Customer confirmation email sent successfully!")
    except Exception as e:
        print(f"[ERROR] Customer email failed: {str(e)}")
    
    print(f"\n2. Testing Admin Notification Email...")
    try:
        send_order_notification_admin_email(latest_order.id)
        print("[OK] Admin notification email sent successfully!")
    except Exception as e:
        print(f"[ERROR] Admin email failed: {str(e)}")
    
    print(f"\n[INFO] Check console output above for email content!")
    print(f"[INFO] If using console backend, emails will be displayed here.")

if __name__ == "__main__":
    test_official_emails()
