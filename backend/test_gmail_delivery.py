#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings

def test_gmail_delivery():
    """Test gửi email đến Gmail với các format khác nhau"""
    
    gmail_address = "nguyenvancong182@gmail.com"
    
    print(f"Testing email delivery to Gmail: {gmail_address}")
    
    # Test 1: Simple text email
    print("\n1. Testing simple text email...")
    try:
        result = send_mail(
            'DBP Sports - Test Email',
            'This is a simple test email from DBP Sports.\n\nIf you receive this, email delivery is working.',
            settings.DEFAULT_FROM_EMAIL,
            [gmail_address],
            fail_silently=False,
        )
        print(f"[OK] Simple email sent: {result}")
    except Exception as e:
        print(f"[ERROR] Simple email failed: {str(e)}")
    
    # Test 2: Email with different subject
    print("\n2. Testing with different subject...")
    try:
        result = send_mail(
            'Order Confirmation - DBP Sports',
            'Your order has been confirmed.\n\nOrder Number: TEST123\nCustomer: Test User\n\nThank you for shopping with DBP Sports!',
            settings.DEFAULT_FROM_EMAIL,
            [gmail_address],
            fail_silently=False,
        )
        print(f"[OK] Confirmation email sent: {result}")
    except Exception as e:
        print(f"[ERROR] Confirmation email failed: {str(e)}")
    
    # Test 3: Email with HTML
    print("\n3. Testing HTML email...")
    try:
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #dc2626;">DBP Sports</h2>
            <p>Dear Customer,</p>
            <p>This is a test HTML email to check delivery.</p>
            <p>If you receive this email, our system is working correctly.</p>
            <p>Best regards,<br>DBP Sports Team</p>
        </body>
        </html>
        """
        
        text_content = """
        DBP Sports
        
        Dear Customer,
        
        This is a test HTML email to check delivery.
        
        If you receive this email, our system is working correctly.
        
        Best regards,
        DBP Sports Team
        """
        
        msg = EmailMultiAlternatives(
            'DBP Sports - HTML Test Email',
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [gmail_address]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        print("[OK] HTML email sent successfully")
    except Exception as e:
        print(f"[ERROR] HTML email failed: {str(e)}")
    
    print(f"\n[INFO] Check {gmail_address} inbox and spam folder!")
    print("[INFO] If emails don't arrive, check Gmail filters and spam settings")

if __name__ == "__main__":
    test_gmail_delivery()
