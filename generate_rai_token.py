#!/usr/bin/env python3
"""
Generate long-lived JWT token for RAI service authentication
"""

from datetime import datetime, timedelta

from jose import jwt

# Get this from your render.com environment variables
SECRET_KEY = input("Enter SECRET_KEY from render.com RAI service: ").strip()

# Token payload
payload = {
    "sub": "pipeline@sni.local",  # Service account identifier
    "role": "analyst",  # Required role for RAI endpoint
    "exp": datetime.utcnow() + timedelta(days=365),  # 1 year expiration
    "iat": datetime.utcnow(),
    "type": "service_token",
}

# Generate token
token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

print("\n" + "=" * 70)
print("RAI SERVICE TOKEN (Valid for 1 year)")
print("=" * 70)
print(f"\n{token}\n")
print("=" * 70)
print("\nAdd this to your .env file:")
print(f"RAI_API_KEY={token}")
print("=" * 70)
