#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from shop.models import Order
from shop.tasks import send_order_confirmation_email, send_order_notification_admin_email
import logging

# Setup logging to see all messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s'
)

def check_email_logs():
    """Kiem tra chi tiet qua trinh gui email"""
    
    latest_order = Order.objects.order_by('-created_at').first()
    if not latest_order:
        print("No orders found")
        return
    
    print(f"=== Checking Email Logs for Order {latest_order.order_number} ===\n")
    
    print("Customer Info:")
    print(f"  Name: {latest_order.customer_name}")
    print(f"  Email: {latest_order.customer_email}")
    print(f"  Phone: {latest_order.customer_phone}")
    
    print("\nOrder Info:")
    print(f"  Order Number: {latest_order.order_number}")
    print(f"  Total: {latest_order.total_amount:,.0f}d")
    print(f"  Status: {latest_order.status}")
    print(f"  Payment Method: {latest_order.payment_method}")
    
    print("\n" + "="*60)
    print("SENDING CUSTOMER EMAIL...")
    print("="*60)
    
    try:
        send_order_confirmation_email(latest_order.id)
        print("\n[SUCCESS] Customer email function completed")
    except Exception as e:
        print(f"\n[ERROR] Customer email failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("SENDING ADMIN EMAIL...")
    print("="*60)
    
    try:
        send_order_notification_admin_email(latest_order.id)
        print("\n[SUCCESS] Admin email function completed")
    except Exception as e:
        print(f"\n[ERROR] Admin email failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("[INFO] Check logs above for any errors")
    print("[INFO] Both functions completed successfully")
    print("[INFO] If emails don't arrive, issue is with Gmail filtering")

if __name__ == "__main__":
    check_email_logs()
