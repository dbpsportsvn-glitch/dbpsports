#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
os.environ.setdefault('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
os.environ.setdefault('FACEBOOK_APP_ID', 'test')
os.environ.setdefault('FACEBOOK_APP_SECRET', 'test')
os.environ.setdefault('FACEBOOK_SECRET_KEY', 'test')
os.environ.setdefault('GOOGLE_OAUTH2_CLIENT_ID', 'test')
os.environ.setdefault('GOOGLE_OAUTH2_CLIENT_SECRET', 'test')

django.setup()

from shop.models import Order
from shop.tasks import send_order_confirmation_email, send_order_notification_admin_email

def send_test_emails():
    """Send test emails"""
    
    # Get latest order
    latest_order = Order.objects.order_by('-created_at').first()
    
    if not latest_order:
        print("No orders found")
        return
    
    print(f"Testing emails for order: {latest_order.order_number}")
    print(f"Customer: {latest_order.customer_name}")
    print(f"Email: {latest_order.customer_email}")
    
    try:
        # Send customer email
        send_order_confirmation_email(latest_order.id)
        print("Customer email sent successfully!")
    except Exception as e:
        print(f"Customer email error: {str(e)}")
    
    try:
        # Send admin email
        send_order_notification_admin_email(latest_order.id)
        print("Admin email sent successfully!")
    except Exception as e:
        print(f"Admin email error: {str(e)}")

if __name__ == "__main__":
    send_test_emails()
