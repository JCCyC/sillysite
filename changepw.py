#!/usr/bin/env python3
"""Change a user's password on the SillySite API.

Usage:
    ./changepw.py <url> <username>
"""

import getpass
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request

PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16


def post_json(url: str, payload: dict, token: str | None = None) -> dict:
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["X-API-Key"] = token
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            body = response.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        detail = error.read().decode()
        raise RuntimeError(f"{error.code} {error.reason}: {detail}") from error


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <url> <username>", file=sys.stderr)
        return 1

    base_url = sys.argv[1].rstrip("/")
    username = sys.argv[2]
    current_password = getpass.getpass("Current password: ")
    new_password = getpass.getpass("New password: ")
    confirm_password = getpass.getpass("Confirm new password: ")

    if new_password != confirm_password:
        print("Change password failed: passwords do not match", file=sys.stderr)
        return 1

    try:
        challenge_data = post_json(f"{base_url}/login/challenge", {"username": username})

        salt = bytes.fromhex(challenge_data["salt"])
        iterations = challenge_data["iterations"]
        challenge = challenge_data["challenge"]

        derived_key = hashlib.pbkdf2_hmac(
            "sha256", current_password.encode(), salt, iterations, dklen=32
        )
        response = hmac.new(derived_key, bytes.fromhex(challenge), hashlib.sha256).hexdigest()

        login_data = post_json(
            f"{base_url}/login/response",
            {"username": username, "challenge": challenge, "response": response},
        )
        token = login_data["token"]

        new_salt = os.urandom(SALT_BYTES)
        new_hash = hashlib.pbkdf2_hmac(
            "sha256", new_password.encode(), new_salt, PBKDF2_ITERATIONS, dklen=32
        )

        post_json(
            f"{base_url}/change-password",
            {
                "new_salt": new_salt.hex(),
                "new_password_hash": new_hash.hex(),
                "new_iterations": PBKDF2_ITERATIONS,
            },
            token=token,
        )
    except (RuntimeError, OSError, KeyError, ValueError) as error:
        print(f"Change password failed: {error}", file=sys.stderr)
        return 1

    print("Password changed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
