#!/usr/bin/env python3
"""
Password Hash Generator for ComfyUI Secure Auth

Generates a PBKDF2-HMAC-SHA256 hash from a password and secret string.
The output hash should be stored in your .env file as AUTH_PASSWORD_HASH.

Usage:
    python scripts/generate-password-hash.py
    python scripts/generate-password-hash.py --non-interactive --password mypass --secret mysecret
"""

import hashlib
import getpass
import sys
import argparse

ITERATIONS = 600_000
ALGORITHM = "sha256"


def generate_hash(password: str, secret: str) -> str:
    """Generate PBKDF2-HMAC-SHA256 hash."""
    hash_bytes = hashlib.pbkdf2_hmac(
        ALGORITHM,
        password.encode("utf-8"),
        secret.encode("utf-8"),
        ITERATIONS,
    )
    return hash_bytes.hex()


def verify_hash(password: str, secret: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash."""
    computed = generate_hash(password, secret)
    return computed == stored_hash


def main():
    parser = argparse.ArgumentParser(description="Generate PBKDF2-HMAC-SHA256 password hash")
    parser.add_argument("--non-interactive", action="store_true", help="Non-interactive mode")
    parser.add_argument("--password", type=str, help="Password (non-interactive mode)")
    parser.add_argument("--secret", type=str, help="Secret string (non-interactive mode)")
    args = parser.parse_args()

    print("")
    print("╔══════════════════════════════════════════╗")
    print("║  ComfyUI Secure Auth — Password Hasher   ║")
    print("║  Algorithm: PBKDF2-HMAC-SHA256            ║")
    print(f"║  Iterations: {ITERATIONS:>28,}  ║")
    print("╚══════════════════════════════════════════╝")
    print("")

    if args.non_interactive:
        if not args.password or not args.secret:
            print("ERROR: --password and --secret are required in non-interactive mode")
            sys.exit(1)
        password = args.password
        secret = args.secret
    else:
        secret = input("Enter your secret string (AUTH_SECRET): ")
        if not secret:
            print("ERROR: Secret string cannot be empty.")
            sys.exit(1)

        password = getpass.getpass("Enter your password: ")
        if not password:
            print("ERROR: Password cannot be empty.")
            sys.exit(1)

        confirm = getpass.getpass("Confirm your password: ")
        if password != confirm:
            print("ERROR: Passwords do not match.")
            sys.exit(1)

    # Generate hash
    password_hash = generate_hash(password, secret)

    # Verify it works
    assert verify_hash(password, secret, password_hash), "Verification failed!"

    print("")
    print("✓ Hash generated and verified successfully!")
    print("")
    print("Add these lines to your .env file:")
    print("─" * 50)
    print(f"AUTH_PASSWORD_HASH={password_hash}")
    print(f"AUTH_SECRET={secret}")
    print("─" * 50)
    print("")


if __name__ == "__main__":
    main()
