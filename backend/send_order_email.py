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

def send_email_for_latest_order():
    """Gửi email cho đơn hàng mới nhất"""
    
    # Lấy đơn hàng mới nhất
    latest_order = Order.objects.order_by('-created_at').first()
    
    if not latest_order:
        print("Không có đơn hàng nào")
        return
    
    print(f"Sending emails for order: {latest_order.order_number}")
    print(f"Customer: {latest_order.customer_name} ({latest_order.customer_email})")
    print(f"Payment method: {latest_order.payment_method}")
    print(f"Total: {latest_order.total_amount}")
    
    # Gửi email xác nhận cho khách hàng
    print("\n1. Sending customer confirmation email...")
    try:
        send_order_confirmation_email(latest_order.id)
        print("[OK] Customer confirmation email sent!")
    except Exception as e:
        print(f"[ERROR] Failed to send customer email: {str(e)}")
    
    # Gửi email thông báo cho admin
    print("\n2. Sending admin notification email...")
    try:
        send_order_notification_admin_email(latest_order.id)
        print("[OK] Admin notification email sent!")
    except Exception as e:
        print(f"[ERROR] Failed to send admin email: {str(e)}")
    
    print(f"\n[INFO] Emails sent for order {latest_order.order_number}")
    print("[INFO] Check your email inbox for the emails!")

def send_email_for_order(order_id):
    """Gửi email cho đơn hàng cụ thể"""
    try:
        order = Order.objects.get(id=order_id)
        
        print(f"Sending emails for order: {order.order_number}")
        print(f"Customer: {order.customer_name} ({order.customer_email})")
        
        # Gửi email xác nhận cho khách hàng
        print("\n1. Sending customer confirmation email...")
        send_order_confirmation_email(order.id)
        print("[OK] Customer confirmation email sent!")
        
        # Gửi email thông báo cho admin
        print("\n2. Sending admin notification email...")
        send_order_notification_admin_email(order.id)
        print("[OK] Admin notification email sent!")
        
        print(f"\n[INFO] Emails sent for order {order.order_number}")
        
    except Order.DoesNotExist:
        print(f"Order with ID {order_id} not found")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Gửi email cho đơn hàng cụ thể
        order_id = int(sys.argv[1])
        send_email_for_order(order_id)
    else:
        # Gửi email cho đơn hàng mới nhất
        send_email_for_latest_order()
