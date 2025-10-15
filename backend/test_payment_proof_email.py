#!/usr/bin/env python
"""
Test email thông báo thanh toán mới cho admin
"""

import os
import sys
import django
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

def test_payment_proof_email():
    """Test email thông báo thanh toán mới"""
    
    # Mock data cho payment proof
    mock_data = {
        'team': {
            'id': 1,
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana',
                'email': 'captain@manutd.com'
            },
            'payment_proof_uploaded_at': timezone.now()
        },
        'tournament': {
            'name': 'Giải bóng đá phong trào 2025',
            'registration_fee': 2000000
        },
        'use_shop_discount': True,
        'cart_total': 500000
    }
    
    # Render template
    html_message = render_to_string('tournaments/emails/new_payment_proof.html', mock_data)
    
    # Tạo file HTML để xem trước
    with open('payment_proof_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao file payment_proof_email.html")
    print("Mo file nay trong browser de xem email")
    
    return True

if __name__ == '__main__':
    try:
        test_payment_proof_email()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
