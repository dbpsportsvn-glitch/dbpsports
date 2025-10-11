#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_different_email_providers():
    """Test gửi email đến các provider khác nhau"""
    
    # Test emails from different providers
    test_emails = [
        'piucotich@gmail.com',           # Gmail
        'piucotich@yahoo.com',           # Yahoo (if exists)
        'piucotich@outlook.com',         # Outlook
        'test@hotmail.com',              # Hotmail
        'admin@dbpsports.com',           # Same domain
    ]
    
    for email in test_emails:
        print(f"\n=== Testing email to: {email} ===")
        
        try:
            result = send_mail(
                'DBP Sports - Email Delivery Test',
                f'This is a test email to verify delivery to {email}.\n\nIf you receive this email, our system is working correctly.\n\nBest regards,\nDBP Sports Team',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            print(f"[OK] Email sent successfully: {result}")
        except Exception as e:
            print(f"[ERROR] Email failed: {str(e)}")

def test_specific_customer_email():
    """Test email cho khách hàng cụ thể"""
    from shop.models import Order
    
    # Get recent orders with different email addresses
    recent_orders = Order.objects.order_by('-created_at')[:3]
    
    for order in recent_orders:
        print(f"\n=== Testing email for order: {order.order_number} ===")
        print(f"Customer: {order.customer_name}")
        print(f"Email: {order.customer_email}")
        
        try:
            result = send_mail(
                f'Order Confirmation #{order.order_number}',
                f'Dear {order.customer_name},\n\nYour order {order.order_number} has been confirmed.\n\nTotal amount: {order.total_amount:,.0f}đ\n\nWe will process your order soon.\n\nThank you for shopping with DBP Sports!',
                settings.DEFAULT_FROM_EMAIL,
                [order.customer_email],
                fail_silently=False,
            )
            print(f"[OK] Email sent to {order.customer_email}: {result}")
        except Exception as e:
            print(f"[ERROR] Email failed to {order.customer_email}: {str(e)}")

if __name__ == "__main__":
    print("=== Email Provider Test ===")
    
    # Test different providers
    test_different_email_providers()
    
    print("\n" + "="*50)
    
    # Test specific customer emails
    test_specific_customer_email()
    
    print(f"\n[INFO] Check all email inboxes and spam folders!")
    print(f"[INFO] If Gmail emails don't arrive but others do, it's a Gmail spam filter issue.")
