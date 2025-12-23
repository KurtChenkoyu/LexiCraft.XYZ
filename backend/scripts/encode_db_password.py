#!/usr/bin/env python3
"""
Helper script to URL-encode database password for connection string.

Usage:
    python3 scripts/encode_db_password.py
    # Enter your password when prompted
    # Copy the encoded output
"""

import urllib.parse
import getpass

def main():
    print("🔐 Database Password URL Encoder")
    print("=" * 50)
    print()
    print("Enter your Supabase database password.")
    print("Special characters will be URL-encoded for the connection string.")
    print()
    
    password = getpass.getpass("Password: ")
    
    if not password:
        print("❌ Error: Password cannot be empty")
        return
    
    encoded = urllib.parse.quote(password, safe='')
    
    print()
    print("=" * 50)
    print("✅ URL-encoded password:")
    print(encoded)
    print()
    print("Use this in your connection string:")
    print(f"postgresql://postgres:{encoded}@db.[PROJECT_REF].supabase.co:6543/postgres?sslmode=require")
    print()

if __name__ == "__main__":
    main()

