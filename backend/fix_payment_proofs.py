#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from shop.models import Order

def fix_payment_proofs():
    """Fix payment proof paths for existing orders"""
    
    # Get orders with payment_proof
    orders = Order.objects.filter(payment_proof__isnull=False)
    
    print(f"Found {orders.count()} orders with payment_proof")
    
    for order in orders:
        print(f"\nProcessing order: {order.order_number}")
        print(f"Current payment_proof: {order.payment_proof}")
        
        if order.payment_proof and order.payment_proof.name:
            # Check if file exists in wrong location
            old_path = f"media/{order.payment_proof.name}"
            new_path = f"media/shop/payment_proofs/{os.path.basename(order.payment_proof.name)}"
            
            print(f"Old path: {old_path}")
            print(f"New path: {new_path}")
            
            if os.path.exists(old_path):
                # Create directory if not exists
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                
                # Move file
                import shutil
                shutil.move(old_path, new_path)
                print(f"Moved file to: {new_path}")
                
                # Update database
                order.payment_proof.name = f"shop/payment_proofs/{os.path.basename(order.payment_proof.name)}"
                order.save()
                print(f"Updated database: {order.payment_proof.name}")
            else:
                print(f"File not found at: {old_path}")
        else:
            print("No payment_proof name found")

if __name__ == "__main__":
    fix_payment_proofs()
    print("\nDone!")
