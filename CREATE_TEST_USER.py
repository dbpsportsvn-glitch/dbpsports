#!/usr/bin/env python
"""
Script để tạo user test với vai trò chuyên gia
Chạy: python CREATE_TEST_USER.py
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
from users.models import Role

def create_test_user():
    print("=== TAO USER TEST ===")
    
    # Tạo user test
    username = "test_professional"
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
                last_name="Professional"
            )
            print(f"Da tao user: {username}")
        
        # Tạo profile nếu chưa có
        profile, created = user.profile
        if created:
            print(f"Da tao profile cho user {username}")
        
        # Lấy vai trò MEDIA
        try:
            media_role = Role.objects.get(id='MEDIA')
            profile.roles.add(media_role)
            print(f"Da them vai tro MEDIA cho user {username}")
        except Role.DoesNotExist:
            print("Khong tim thay vai tro MEDIA")
            
        # Kiểm tra vai trò của user
        roles = profile.roles.all()
        print(f"Vai tro cua user {username}:")
        for role in roles:
            print(f"  - {role.id}: {role.name}")
            
    except Exception as e:
        print(f"Loi: {e}")

if __name__ == "__main__":
    create_test_user()
