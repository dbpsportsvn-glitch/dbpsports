#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from shop.models import Order
from django.core.mail import send_mail
from django.conf import settings

def test_simple_email():
    """Test gửi email đơn giản"""
    print("=== Testing Simple Email ===")
    try:
        result = send_mail(
            'Test Email - DBP Sports',
            'This is a test email from DBP Sports system.',
            settings.DEFAULT_FROM_EMAIL,
            ['test@example.com'],
            fail_silently=False,
        )
        print(f"Email sent successfully: {result}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def test_email_with_console():
    """Test email với console backend"""
    print("\n=== Testing with Console Backend ===")
    
    # Temporarily change to console backend
    original_backend = settings.EMAIL_BACKEND
    settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    
    try:
        result = send_mail(
            'Test Console Email - DBP Sports',
            'This is a test email using console backend.',
            settings.DEFAULT_FROM_EMAIL,
            ['console@example.com'],
            fail_silently=False,
        )
        print(f"Console email sent successfully: {result}")
        return True
    except Exception as e:
        print(f"Error sending console email: {str(e)}")
        return False
    finally:
        # Restore original backend
        settings.EMAIL_BACKEND = original_backend

def test_order_email():
    """Test email với đơn hàng thực tế"""
    print("\n=== Testing Order Email ===")
    
    # Lấy đơn hàng gần nhất
    latest_order = Order.objects.order_by('-created_at').first()
    
    if not latest_order:
        print("Không có đơn hàng nào để test")
        return False
    
    print(f"Testing with order: {latest_order.order_number}")
    print(f"Customer: {latest_order.customer_name} ({latest_order.customer_email})")
    
    # Import và test email functions
    from shop.tasks import send_order_confirmation_email, send_order_notification_admin_email
    
    print("\n1. Testing customer confirmation email...")
    try:
        send_order_confirmation_email(latest_order.id)
        print("[OK] Customer confirmation email sent successfully!")
    except Exception as e:
        print(f"[ERROR] Error sending customer email: {str(e)}")
        return False
    
    print("\n2. Testing admin notification email...")
    try:
        send_order_notification_admin_email(latest_order.id)
        print("[OK] Admin notification email sent successfully!")
    except Exception as e:
        print(f"[ERROR] Error sending admin email: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== DBP Sports Email Debug ===")
    
    # Test 1: Simple email
    simple_ok = test_simple_email()
    
    # Test 2: Console email
    console_ok = test_email_with_console()
    
    # Test 3: Order email
    order_ok = test_order_email()
    
    print(f"\n=== Results ===")
    print(f"Simple Email: {'OK' if simple_ok else 'FAILED'}")
    print(f"Console Email: {'OK' if console_ok else 'FAILED'}")
    print(f"Order Email: {'OK' if order_ok else 'FAILED'}")
    
    if not any([simple_ok, console_ok, order_ok]):
        print("\n[INFO] All email tests failed. Check email configuration.")
    else:
        print("\n[INFO] Some email tests passed. Check your email inbox or console output.")
