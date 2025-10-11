#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from shop.models import Order
from django.contrib.auth.models import User

def test_upload():
    """Test upload payment proof"""
    
    # Get a test order
    order = Order.objects.filter(payment_proof__isnull=True).first()
    
    if not order:
        print("No orders without payment proof found")
        return
    
    print(f"Testing with order: {order.order_number}")
    
    # Create a test file
    test_content = b"This is a test payment proof file"
    test_file = SimpleUploadedFile(
        "test_payment_proof.txt",
        test_content,
        content_type="text/plain"
    )
    
    # Upload file
    order.payment_proof = test_file
    order.save()
    
    print(f"Uploaded file: {order.payment_proof}")
    print(f"File name: {order.payment_proof.name}")
    print(f"File URL: {order.payment_proof.url}")
    print(f"File exists: {order.payment_proof.storage.exists(order.payment_proof.name)}")
    
    # Check if file exists in filesystem
    file_path = f"media/{order.payment_proof.name}"
    print(f"File path: {file_path}")
    print(f"File exists in filesystem: {os.path.exists(file_path)}")

if __name__ == "__main__":
    test_upload()
    print("\nTest completed!")
