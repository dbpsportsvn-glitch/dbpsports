#!/usr/bin/env python
"""
Test email thông báo đội mới đăng ký cho admin và BTC
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

def test_team_registration_email():
    """Test email thông báo đội mới đăng ký"""
    
    # Mock data cho team registration
    mock_data = {
        'team': {
            'id': 1,
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana',
                'email': 'captain@manutd.com'
            },
            'players': {'count': 15},
            'address': '123 Đường ABC, Quận 1, TP.HCM',
            'phone': '0901234567',
            'tournament': {
                'name': 'Giải bóng đá phong trào 2025',
                'registration_fee': 2000000
            }
        },
        'tournament': {
            'name': 'Giải bóng đá phong trào 2025',
            'registration_fee': 2000000
        },
        'registration': {
            'registered_at': timezone.now()
        }
    }
    
    # Render template
    html_message = render_to_string('tournaments/emails/new_team_registration.html', mock_data)
    
    # Tạo file HTML để xem trước
    with open('team_registration_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao file team_registration_email.html")
    print("Mo file nay trong browser de xem email")
    
    return True

if __name__ == '__main__':
    try:
        test_team_registration_email()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
