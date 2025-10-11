#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from shop.models import PaymentMethod

# Fix encoding issue
try:
    payment_method = PaymentMethod.objects.get(payment_type='e_wallet')
    
    # Delete the corrupted one
    payment_method.delete()
    print("Deleted corrupted payment method")
    
    # Create new one with correct encoding
    new_payment_method = PaymentMethod.objects.create(
        name='Ví điện tử',
        payment_type='e_wallet',
        description='Thanh toán qua Momo, ZaloPay, VNPay',
        icon='fas fa-wallet',
        is_active=True,
        order=2
    )
    
    print(f"Created new payment method: {new_payment_method.name}")
    print("Encoding fixed!")
    
except Exception as e:
    print(f"Error: {e}")
