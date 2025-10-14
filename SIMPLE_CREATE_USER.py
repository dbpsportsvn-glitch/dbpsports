#!/usr/bin/env python
"""
Script đơn giản để tạo user test
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from django.contrib.auth.models import User

def create_simple_user():
    print("=== TAO USER DON GIAN ===")
    
    # Tạo user test
    username = "testuser"
    email = "test@example.com"
    
    try:
        # Kiểm tra user đã tồn tại chưa
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            print(f"User {username} da ton tai")
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password="test123",
                first_name="Test",
                last_name="User"
            )
            print(f"Da tao user: {username} (email: {email}, password: test123)")
            
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        
    except Exception as e:
        print(f"Loi: {e}")

if __name__ == "__main__":
    create_simple_user()
