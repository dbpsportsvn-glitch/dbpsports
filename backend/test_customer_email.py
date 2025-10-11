#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from shop.models import Order

def test_customer_email_direct():
    """Test gửi email trực tiếp cho khách hàng"""
    
    # Lấy đơn hàng mới nhất
    latest_order = Order.objects.order_by('-created_at').first()
    
    if not latest_order:
        print("Không có đơn hàng nào")
        return
    
    customer_email = latest_order.customer_email
    print(f"Testing email for customer: {customer_email}")
    print(f"Order: {latest_order.order_number}")
    
    # Test 1: Simple email
    print("\n1. Testing simple email...")
    try:
        result = send_mail(
            f'Test Email - Đơn hàng #{latest_order.order_number}',
            f'Xin chào {latest_order.customer_name},\n\nĐây là email test cho đơn hàng {latest_order.order_number}.\n\nTrân trọng,\nDBP Sports',
            settings.DEFAULT_FROM_EMAIL,
            [customer_email],
            fail_silently=False,
        )
        print(f"[OK] Simple email sent successfully: {result}")
    except Exception as e:
        print(f"[ERROR] Simple email failed: {str(e)}")
    
    # Test 2: HTML email
    print("\n2. Testing HTML email...")
    try:
        html_content = f"""
        <html>
        <body>
            <h1>Test HTML Email</h1>
            <p>Xin chào <strong>{latest_order.customer_name}</strong>,</p>
            <p>Đây là email test HTML cho đơn hàng <strong>{latest_order.order_number}</strong>.</p>
            <p>Trân trọng,<br>DBP Sports</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Xin chào {latest_order.customer_name},
        
        Đây là email test cho đơn hàng {latest_order.order_number}.
        
        Trân trọng,
        DBP Sports
        """
        
        msg = EmailMultiAlternatives(
            f'Test HTML Email - Đơn hàng #{latest_order.order_number}',
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [customer_email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        print("[OK] HTML email sent successfully")
    except Exception as e:
        print(f"[ERROR] HTML email failed: {str(e)}")
    
    # Test 3: Template email
    print("\n3. Testing template email...")
    try:
        from shop.tasks import send_order_confirmation_email
        send_order_confirmation_email(latest_order.id)
        print("[OK] Template email sent successfully")
    except Exception as e:
        print(f"[ERROR] Template email failed: {str(e)}")

def test_email_to_different_address():
    """Test gửi email đến địa chỉ khác"""
    print("\n=== Testing email to different address ===")
    
    test_emails = [
        'nguyenvancong182@gmail.com',
        'test@gmail.com',
        'admin@dbpsports.com'
    ]
    
    for email in test_emails:
        print(f"\nTesting email to: {email}")
        try:
            result = send_mail(
                'Test Email - DBP Sports',
                f'This is a test email sent to {email}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            print(f"[OK] Email sent to {email}: {result}")
        except Exception as e:
            print(f"[ERROR] Email failed to {email}: {str(e)}")

if __name__ == "__main__":
    print("=== Customer Email Debug ===")
    
    # Test customer email
    test_customer_email_direct()
    
    # Test different addresses
    test_email_to_different_address()
    
    print("\n[INFO] Check your email inbox for test emails!")
