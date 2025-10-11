#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from shop.models import PaymentMethod, BankAccount

def create_payment_data():
    print("Creating payment data...")
    
    # Create PaymentMethod first
    bank_method, created = PaymentMethod.objects.get_or_create(
        name="Chuyen khoan ngan hang",
        defaults={
            'payment_type': 'bank_transfer',
            'description': 'Thanh toan qua chuyen khoan ngan hang',
            'icon': 'fas fa-university',
            'order': 1,
            'is_active': True
        }
    )
    print(f"PaymentMethod: {bank_method.name} {'(created)' if created else '(already exists)'}")
    
    # Create BankAccount
    bank_account, created = BankAccount.objects.get_or_create(
        payment_method=bank_method,
        bank_name='VietinBank',
        defaults={
            'account_holder': 'DBP Sports',
            'account_number': '1234567890',
            'branch': 'Ha Noi',
            'order': 1,
            'is_active': True
        }
    )
    print(f"BankAccount: {bank_account.bank_name} - {bank_account.account_number} {'(created)' if created else '(already exists)'}")
    
    print("Done! You can now add bank accounts in Django Admin.")

if __name__ == '__main__':
    create_payment_data()
