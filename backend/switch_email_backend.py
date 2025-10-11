#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def switch_to_console_email():
    """Switch email backend to console for development"""
    
    env_file = '.env'
    
    # Check if .env file exists
    if not os.path.exists(env_file):
        print("Creating .env file...")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Email Backend\n")
            f.write("EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend\n")
        print("✅ Created .env file with console email backend")
    else:
        # Read existing .env file
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update or add EMAIL_BACKEND
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('EMAIL_BACKEND='):
                lines[i] = 'EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend\n'
                updated = True
                break
        
        if not updated:
            lines.append('EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend\n')
        
        # Write back to .env file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Updated .env file to use console email backend")
    
    print("\n📧 Email backend switched to console!")
    print("📝 Restart Django server to apply changes")
    print("📋 Emails will now appear in console output instead of being sent via SMTP")

def switch_to_smtp_email():
    """Switch email backend to SMTP for production"""
    
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print("Creating .env file...")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Email Backend\n")
            f.write("EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend\n")
        print("✅ Created .env file with SMTP email backend")
    else:
        # Read existing .env file
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update or add EMAIL_BACKEND
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('EMAIL_BACKEND='):
                lines[i] = 'EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend\n'
                updated = True
                break
        
        if not updated:
            lines.append('EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend\n')
        
        # Write back to .env file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Updated .env file to use SMTP email backend")
    
    print("\n📧 Email backend switched to SMTP!")
    print("📝 Restart Django server to apply changes")
    print("📋 Emails will now be sent via SMTP to real email addresses")

if __name__ == "__main__":
    print("=== Email Backend Switcher ===")
    print("1. Switch to Console (for development)")
    print("2. Switch to SMTP (for production)")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "1":
        switch_to_console_email()
    elif choice == "2":
        switch_to_smtp_email()
    else:
        print("Invalid choice. Please run the script again.")
