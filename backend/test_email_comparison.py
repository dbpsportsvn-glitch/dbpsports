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
from shop.tasks import send_order_confirmation_email

def test_email_comparison():
    """So sánh email test vs email shop"""
    
    test_email = 'piucotich@gmail.com'
    
    print("=== Test 1: Email don gian (nhu email test truoc do) ===")
    try:
        result = send_mail(
            'DBP Sports - Test Email',
            'Day la email test don gian. Neu ban nhan duoc email nay, he thong hoat dong tot!',
            settings.DEFAULT_FROM_EMAIL,
            [test_email],
            fail_silently=False,
        )
        print(f"[OK] Email test sent: {result}")
        print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
    
    print("\n=== Test 2: Email xac nhan don hang (shop) ===")
    try:
        latest_order = Order.objects.order_by('-created_at').first()
        if latest_order:
            send_order_confirmation_email(latest_order.id)
            print(f"[OK] Shop email sent for order {latest_order.order_number}")
            print(f"To: {latest_order.customer_email}")
        else:
            print("[ERROR] No orders found")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
    
    print("\n=== Kiem tra cau hinh ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    
    print("\n[INFO] Check email inbox for both emails!")
    print("[INFO] If only test email arrives, the issue is with shop email template/content")

if __name__ == "__main__":
    test_email_comparison()
