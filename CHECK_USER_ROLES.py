#!/usr/bin/env python
"""
Script để kiểm tra vai trò của user
Chạy: python CHECK_USER_ROLES.py
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

def check_user_roles():
    print("=== KIEM TRA VAI TRO USER ===")
    
    # Lấy tất cả users
    users = User.objects.all()
    print(f"Tong so users: {users.count()}")
    
    for user in users:
        print(f"\nUser: {user.username} ({user.email})")
        
        # Kiểm tra profile
        try:
            profile = user.profile
            print(f"  Profile: Có")
            
            # Lấy vai trò
            roles = profile.roles.all()
            print(f"  So vai tro: {roles.count()}")
            
            if roles.exists():
                print("  Vai tro:")
                for role in roles:
                    print(f"    - {role.id}: {role.name}")
                    
                # Kiểm tra vai trò chuyên gia
                professional_role_ids = ['COACH', 'COMMENTATOR', 'MEDIA', 'PHOTOGRAPHER', 'REFEREE']
                user_role_ids = list(roles.values_list('id', flat=True))
                professional_roles = [role_id for role_id in user_role_ids if role_id in professional_role_ids]
                
                if professional_roles:
                    print(f"  Vai tro chuyen gia: {professional_roles}")
                else:
                    print("  Vai tro chuyen gia: KHONG CO")
            else:
                print("  Vai tro: KHONG CO")
                
        except Exception as e:
            print(f"  Profile: LOI - {e}")
    
    print("\n=== KIEM TRA ROLES CO SAN ===")
    try:
        roles = Role.objects.all()
        print(f"Tong so roles: {roles.count()}")
        for role in roles:
            print(f"  - {role.id}: {role.name}")
    except Exception as e:
        print(f"Loi khi lay roles: {e}")

if __name__ == "__main__":
    check_user_roles()
