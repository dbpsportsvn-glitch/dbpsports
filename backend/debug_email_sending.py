#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from shop.models import Order
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_send_order_email():
    """Debug email sending process"""
    
    latest_order = Order.objects.order_by('-created_at').first()
    if not latest_order:
        print("No orders found")
        return
    
    print(f"=== Debugging Email for Order {latest_order.order_number} ===")
    print(f"Customer: {latest_order.customer_name}")
    print(f"Email: {latest_order.customer_email}")
    
    # Render template
    print("\n1. Rendering template...")
    try:
        html_content = render_to_string('shop/emails/order_confirmation_simple.html', {
            'order': latest_order,
            'request': type('obj', (object,), {
                'scheme': 'http',
                'get_host': lambda: 'localhost:8000'
            })
        })
        print(f"[OK] Template rendered: {len(html_content)} characters")
    except Exception as e:
        print(f"[ERROR] Template render failed: {str(e)}")
        return
    
    # Create plain text
    print("\n2. Creating plain text version...")
    text_content = f"""
Xin chao {latest_order.customer_name},

Cam on ban da dat hang tai DBP Sports!

Thong tin don hang:
- Ma don hang: {latest_order.order_number}
- Ngay dat: {latest_order.created_at.strftime('%d/%m/%Y %H:%M')}
- Tong tien: {latest_order.total_amount:,.0f}d
- Trang thai: {latest_order.get_status_display()}

Chung toi se xu ly don hang cua ban trong thoi gian som nhat.

Tran trong,
Doi ngu DBP Sports
    """
    print(f"[OK] Plain text created: {len(text_content)} characters")
    
    # Create email
    print("\n3. Creating email message...")
    subject = f'Xac nhan don hang #{latest_order.order_number} - DBP Sports'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [latest_order.customer_email]
    
    print(f"Subject: {subject}")
    print(f"From: {from_email}")
    print(f"To: {to_email}")
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    
    # Send email
    print("\n4. Sending email...")
    try:
        result = msg.send()
        print(f"[OK] Email sent successfully: {result}")
    except Exception as e:
        print(f"[ERROR] Email send failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n5. Comparing with simple test email...")
    print("Sending simple test email to same address...")
    from django.core.mail import send_mail
    try:
        result = send_mail(
            'Test - Simple Email',
            'This is a simple test email.',
            from_email,
            to_email,
            fail_silently=False,
        )
        print(f"[OK] Simple email sent: {result}")
    except Exception as e:
        print(f"[ERROR] Simple email failed: {str(e)}")
    
    print("\n[INFO] Check your email inbox!")
    print("[INFO] If simple email arrives but order email doesn't:")
    print("  - Check spam folder")
    print("  - Issue is with email content/subject")
    print("  - Try different subject line")

if __name__ == "__main__":
    debug_send_order_email()
