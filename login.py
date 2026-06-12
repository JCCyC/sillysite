#!/usr/bin/env python3
"""Log in to the Silly Site API and print a session token.

Usage:
    ./login.py <url> <username>
"""

import getpass
import hashlib
import hmac
import json
import sys
import urllib.error
import urllib.request


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode()
        raise RuntimeError(f"{error.code} {error.reason}: {detail}") from error


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <url> <username>", file=sys.stderr)
        return 1

    base_url = sys.argv[1].rstrip("/")
    username = sys.argv[2]
    password = getpass.getpass("Password: ")

    try:
        challenge_data = post_json(f"{base_url}/login/challenge", {"username": username})

        salt = bytes.fromhex(challenge_data["salt"])
        iterations = challenge_data["iterations"]
        challenge = challenge_data["challenge"]

        derived_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations, dklen=32)
        response = hmac.new(derived_key, bytes.fromhex(challenge), hashlib.sha256).hexdigest()

        login_data = post_json(
            f"{base_url}/login/response",
            {"username": username, "challenge": challenge, "response": response},
        )
    except (RuntimeError, OSError, KeyError, ValueError) as error:
        print(f"Login failed: {error}", file=sys.stderr)
        return 1

    print(login_data["token"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
