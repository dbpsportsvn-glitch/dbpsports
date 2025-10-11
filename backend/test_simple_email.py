#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from shop.models import Order

def send_simple_order_confirmation(order_id):
    """Gửi email xác nhận đơn giản cho khách hàng"""
    try:
        order = Order.objects.get(id=order_id)
        
        # Render simple email template
        html_content = render_to_string('shop/emails/simple_order_confirmation.html', {
            'order': order,
        })
        
        # Create simple text version
        text_content = f"""
Xin chào {order.customer_name},

Cảm ơn bạn đã đặt hàng tại DBP Sports!

THÔNG TIN ĐƠN HÀNG:
- Mã đơn hàng: {order.order_number}
- Ngày đặt: {order.created_at.strftime('%d/%m/%Y %H:%M')}
- Tổng tiền: {order.total_amount:,.0f}đ
- Phương thức thanh toán: {order.get_payment_method_display()}

SẢN PHẨM ĐÃ ĐẶT:
"""
        
        for item in order.orderitem_set.all():
            text_content += f"- {item.product.name} x {item.quantity} = {item.total_price:,.0f}đ\n"
        
        text_content += f"""
THÔNG TIN GIAO HÀNG:
- Người nhận: {order.customer_name}
- Số điện thoại: {order.customer_phone}
- Địa chỉ: {order.shipping_address}, {order.shipping_district}, {order.shipping_city}

Chúng tôi sẽ xử lý đơn hàng của bạn trong thời gian sớm nhất.

Trân trọng,
Đội ngũ DBP Sports
        """
        
        # Create email
        subject = f'Xác nhận đơn hàng #{order.order_number} - DBP Sports'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [order.customer_email]
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        print(f"Simple confirmation email sent to {order.customer_email} for order {order.order_number}")
        return True
        
    except Order.DoesNotExist:
        print(f"Order {order_id} not found")
        return False
    except Exception as e:
        print(f"Error sending simple email: {str(e)}")
        return False

def test_different_email_formats(order_id):
    """Test các format email khác nhau"""
    order = Order.objects.get(id=order_id)
    customer_email = order.customer_email
    
    print(f"Testing different email formats for: {customer_email}")
    
    # Test 1: Plain text only
    print("\n1. Testing plain text email...")
    try:
        from django.core.mail import send_mail
        result = send_mail(
            f'Order Confirmation #{order.order_number}',
            f'Dear {order.customer_name},\n\nYour order {order.order_number} has been confirmed.\n\nTotal: {order.total_amount:,.0f}đ\n\nThank you!\nDBP Sports',
            settings.DEFAULT_FROM_EMAIL,
            [customer_email],
            fail_silently=False,
        )
        print(f"[OK] Plain text email sent: {result}")
    except Exception as e:
        print(f"[ERROR] Plain text email failed: {str(e)}")
    
    # Test 2: Simple HTML
    print("\n2. Testing simple HTML email...")
    try:
        send_simple_order_confirmation(order_id)
        print("[OK] Simple HTML email sent")
    except Exception as e:
        print(f"[ERROR] Simple HTML email failed: {str(e)}")
    
    # Test 3: Different subject line
    print("\n3. Testing different subject line...")
    try:
        result = send_mail(
            'Your order is confirmed',
            f'Dear {order.customer_name},\n\nYour order {order.order_number} has been confirmed.\n\nThank you for shopping with us!\n\nDBP Sports Team',
            settings.DEFAULT_FROM_EMAIL,
            [customer_email],
            fail_silently=False,
        )
        print(f"[OK] Different subject email sent: {result}")
    except Exception as e:
        print(f"[ERROR] Different subject email failed: {str(e)}")

if __name__ == "__main__":
    # Get latest order
    latest_order = Order.objects.order_by('-created_at').first()
    
    if latest_order:
        print(f"Testing with order: {latest_order.order_number}")
        print(f"Customer: {latest_order.customer_name} ({latest_order.customer_email})")
        
        test_different_email_formats(latest_order.id)
        
        print(f"\n[INFO] Check {latest_order.customer_email} inbox and spam folder!")
    else:
        print("No orders found")
