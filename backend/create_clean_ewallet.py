#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from shop.models import PaymentMethod, EWalletAccount

try:
    # Delete all e-wallet related data
    EWalletAccount.objects.filter(payment_method__payment_type='e_wallet').delete()
    PaymentMethod.objects.filter(payment_type='e_wallet').delete()
    print("Cleaned up old data")
    
    # Create new payment method (using ASCII characters only)
    payment_method = PaymentMethod.objects.create(
        name='Vi Dien Tu',
        payment_type='e_wallet',
        description='Thanh toan qua Momo, ZaloPay, VNPay',
        icon='fas fa-wallet',
        is_active=True,
        order=2
    )
    
    # Recreate e-wallets
    ewallets = [
        {'wallet_name': 'Momo', 'account_info': '0901234567', 'order': 1},
        {'wallet_name': 'ZaloPay', 'account_info': '0901234567', 'order': 2},
        {'wallet_name': 'VNPay', 'account_info': '0901234567', 'order': 3},
    ]
    
    for data in ewallets:
        EWalletAccount.objects.create(
            payment_method=payment_method,
            wallet_name=data['wallet_name'],
            account_info=data['account_info'],
            order=data['order'],
            is_active=True
        )
    
    print("Created clean e-wallet data")
    print("Now you can update the name in Django Admin with proper UTF-8")
    
except Exception as e:
    print(f"Error: {e}")
