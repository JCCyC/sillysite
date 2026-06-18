#!/usr/bin/env python3
"""Drives a real headless Chrome through login.html -> whoami.html ->
changepw.html -> re-login, over the plain WebDriver HTTP protocol (no
selenium/puppeteer needed -- just chromedriver + stdlib urllib). This is
the only place the project's *browser-side* crypto.subtle/fetch code path
gets exercised end to end (the Node test suite only covers the Node-side
branch of js/sillysite.js).

Usage: browser_e2e.py <base_url> <username> <password> <new_password>
Exits 0 on success, 1 with a message on stderr otherwise. Manages its own
chromedriver subprocess.
"""
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class WebDriver:
    def __init__(self, port):
        self.base = f"http://127.0.0.1:{port}"
        self.session = None

    def _call(self, method, path, body=None):
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(body if body is not None else {}).encode(),
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())["value"]

    def wait_ready(self, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if self._call("GET", "/status").get("ready"):
                    return True
            except (urllib.error.URLError, ConnectionError):
                pass
            time.sleep(0.2)
        return False

    def start_session(self):
        caps = {
            "capabilities": {
                "alwaysMatch": {
                    "browserName": "chrome",
                    "goog:chromeOptions": {
                        "args": ["--headless=new", "--no-sandbox", "--disable-gpu"]
                    },
                }
            }
        }
        self.session = self._call("POST", "/session", caps)["sessionId"]

    def quit(self):
        if self.session:
            try:
                self._call("DELETE", f"/session/{self.session}")
            except (urllib.error.URLError, ConnectionError):
                pass

    def navigate(self, url):
        self._call("POST", f"/session/{self.session}/url", {"url": url})

    def current_url(self):
        return self._call("GET", f"/session/{self.session}/url")

    def find(self, css):
        return self._call(
            "POST", f"/session/{self.session}/element", {"using": "css selector", "value": css}
        )["element-6066-11e4-a52e-4f735466cecf"]

    def send_keys(self, css, text):
        el = self.find(css)
        self._call("POST", f"/session/{self.session}/element/{el}/value", {"text": text})

    def click(self, css):
        el = self.find(css)
        self._call("POST", f"/session/{self.session}/element/{el}/click")

    def text(self, css):
        el = self.find(css)
        return self._call("GET", f"/session/{self.session}/element/{el}/text")


def main():
    base_url, username, password, new_password = sys.argv[1:5]

    port = find_free_port()
    proc = subprocess.Popen(
        ["chromedriver", f"--port={port}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    driver = WebDriver(port)
    try:
        if not driver.wait_ready():
            print("chromedriver did not become ready", file=sys.stderr)
            return 1

        driver.start_session()

        driver.navigate(f"{base_url}/login.html")
        driver.send_keys("#username", username)
        driver.send_keys("#password", password)
        driver.click("#submit-button")
        time.sleep(1.5)

        url = driver.current_url()
        if "/whoami.html?apikey=" not in url:
            print(f"login: expected redirect to whoami.html, got {url}", file=sys.stderr)
            return 1
        apikey = url.split("apikey=")[1]

        shown_username = driver.text("#username")
        if shown_username != username:
            print(f"whoami: expected username {username!r}, got {shown_username!r}", file=sys.stderr)
            return 1

        driver.navigate(f"{base_url}/changepw.html?apikey={apikey}")
        time.sleep(0.5)
        expected_title = f"Password change for {username}"
        title = driver.text("#title")
        if title != expected_title:
            print(f"changepw: expected title {expected_title!r}, got {title!r}", file=sys.stderr)
            return 1

        driver.send_keys("#current-password", password)
        driver.send_keys("#new-password", new_password)
        driver.send_keys("#confirm-password", new_password)
        driver.click("#submit-button")
        time.sleep(1.5)

        msg = driver.text("#message")
        if msg != "Password changed successfully":
            print(f"changepw: expected success message, got {msg!r}", file=sys.stderr)
            return 1

        driver.navigate(f"{base_url}/login.html")
        driver.send_keys("#username", username)
        driver.send_keys("#password", password)
        driver.click("#submit-button")
        time.sleep(1.5)
        if "/whoami.html" in driver.current_url():
            print("login: old password unexpectedly still works", file=sys.stderr)
            return 1

        driver.navigate(f"{base_url}/login.html")
        driver.send_keys("#username", username)
        driver.send_keys("#password", new_password)
        driver.click("#submit-button")
        time.sleep(1.5)
        final_url = driver.current_url()
        if "/whoami.html?apikey=" not in final_url:
            print(f"login: new password did not work, got {final_url}", file=sys.stderr)
            return 1

        return 0
    finally:
        driver.quit()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
