#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from django.conf import settings
from shop.models import Order

def check_email_configuration():
    """Kiểm tra cấu hình email"""
    print("=== Email Configuration Check ===")
    
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    
    # Check admin emails
    admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
    print(f"ADMIN_EMAILS: {admin_emails}")

def check_recent_orders():
    """Kiểm tra đơn hàng gần đây"""
    print("\n=== Recent Orders Check ===")
    
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    for order in recent_orders:
        print(f"\nOrder: {order.order_number}")
        print(f"  Customer: {order.customer_name}")
        print(f"  Email: {order.customer_email}")
        print(f"  Payment Method: {order.payment_method}")
        print(f"  Created: {order.created_at}")
        print(f"  Status: {order.status}")

def suggest_solutions():
    """Đề xuất giải pháp"""
    print("\n=== Possible Solutions ===")
    
    print("1. 📧 Check Spam/Junk Folder")
    print("   - Gmail: Check 'Spam' folder")
    print("   - Yahoo: Check 'Spam' folder") 
    print("   - Outlook: Check 'Junk Email' folder")
    
    print("\n2. 📱 Check Email Filters")
    print("   - Gmail: Settings > Filters and Blocked Addresses")
    print("   - Look for filters blocking emails from 'dbpsports.com'")
    
    print("\n3. 🔍 Check Email Address")
    print("   - Verify the customer email address is correct")
    print("   - Make sure there are no typos")
    
    print("\n4. 📨 Email Provider Issues")
    print("   - Some email providers block emails from certain domains")
    print("   - Try sending to a different email provider (Gmail, Yahoo, etc.)")
    
    print("\n5. 🛠️ Test with Different Email")
    print("   - Try placing an order with a different email address")
    print("   - Use a Gmail or Yahoo email for testing")

if __name__ == "__main__":
    check_email_configuration()
    check_recent_orders()
    suggest_solutions()
    
    print(f"\n=== Next Steps ===")
    print("1. Ask customer to check Spam/Junk folder")
    print("2. Verify email address is correct")
    print("3. Try sending to a different email address")
    print("4. Check email filters and settings")
