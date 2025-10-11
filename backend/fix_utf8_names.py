#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from shop.models import PaymentMethod

try:
    # Get the payment method
    payment_method = PaymentMethod.objects.get(payment_type='e_wallet')
    
    # Update with proper UTF-8 names
    payment_method.name = 'Ví điện tử'
    payment_method.description = 'Thanh toán qua Momo, ZaloPay, VNPay'
    payment_method.save()
    
    print("Successfully updated payment method names with Vietnamese diacritics!")
    print(f"Name: {payment_method.name}")
    print(f"Description: {payment_method.description}")
    
except PaymentMethod.DoesNotExist:
    print("E-wallet payment method not found!")
except Exception as e:
    print(f"Error: {e}")
