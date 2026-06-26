# SillySite PHP client library

A PHP library (`Sillysite`) and two command-line scripts that interact with
the SillySite API.

## Prerequisites

```
sudo apt-get install php-cli
```

Confirmed against PHP 8.2 (Debian 12's `php-cli` package). No other
dependencies: the library uses only core PHP -- stream contexts for HTTP
(no `curl` extension needed) and the `hash`/`json` extensions, both enabled
by default in a plain `php-cli` install with no separate package. No
Composer, no `vendor/`, no autoloader -- just `require` the files directly.

## Running the CLI scripts

```
php login.php <baseurl> <username>
php changepw.php <baseurl> <username>
```

or, since they're executable with a `#!/usr/bin/env php` shebang:

```
./login.php <baseurl> <username>
./changepw.php <baseurl> <username>
```

---

## Library API (`Sillysite.php`)

```php
require __DIR__ . "/Sillysite.php";
```

No namespace, no Composer autoloading -- just `require` it, the same as
`require __DIR__ . "/Readpass.php"` for the CLI scripts' password prompt.

### Response type

```php
final class SillysiteResponse
{
    public readonly int $status;     // HTTP status code, or 0 on transport error
    public readonly ?string $body;   // response body, or null
    public readonly ?string $error;  // transport error description, or null
}
```

`status === 0` means a transport-level failure (no HTTP response was
received); `error` describes it. Otherwise `status` is the real HTTP status
code and `error` is `null`.

### SillysiteException

The high-level auth methods below throw `SillysiteException` on failure,
carrying the HTTP `status` and response `body` alongside the message:

```php
final class SillysiteException extends \Exception
{
    public readonly int $status;
    public readonly ?string $body;
}
```

---

### High-level auth methods

#### `Sillysite::login`

```php
public static function login(string $baseUrl, string $username, string $password): string
```

Performs the full challenge/response login flow and returns the session
token. The password is used locally to derive a PBKDF2-HMAC-SHA256 key and
then an HMAC-SHA256 response; the plaintext password is never sent over the
network.

Unlike the C/Java/JS/C# bindings, passwords here are plain `string`, not a
char-array/byte-array type the caller can wipe after use: PHP strings are
immutable values with no reliable in-userland way to zero the underlying
memory, so there's no real wiping to do in PHP regardless of the parameter
type.

**Example:**
```php
try {
    $token = Sillysite::login("http://localhost:8000", "alice", "s3cret");
    // use $token ...
} catch (SillysiteException $e) {
    fwrite(STDERR, "login failed: " . $e->getMessage() . "\n");
}
```

---

#### `Sillysite::changepw`

```php
public static function changepw(string $baseUrl, string $username, string $oldPassword, string $newPassword): void
```

Changes the user's password. Internally logs in with `$oldPassword` to get
a session token, derives a fresh PBKDF2 salt/hash from `$newPassword`
locally, and posts the derived values to `/change-password`. The new
password is never sent over the network.

---

#### `Sillysite::logout`

```php
public static function logout(string $baseUrl, string $apiKey): ?string
```

Invalidates the session identified by `$apiKey`. Returns the server's
confirmation message (e.g. `"User alice logged out"`). Throws if called
with the static `.env` `API_KEY`, which has no session to invalidate.

---

### Raw HTTP helpers

All four helpers construct the URL as `$baseUrl + $path`, send the request
with an optional `X-API-Key` header, and never throw -- transport failures
are reported through the returned `SillysiteResponse` (`status = 0`,
`error` set), the same as an ordinary HTTP error response.

```php
public static function get(string $baseUrl, ?string $apiKey, string $path): SillysiteResponse
public static function post(string $baseUrl, ?string $apiKey, string $path, ?string $jsonBody): SillysiteResponse
public static function put(string $baseUrl, ?string $apiKey, string $path, ?string $jsonBody): SillysiteResponse
public static function delete(string $baseUrl, ?string $apiKey, string $path): SillysiteResponse
```

`$jsonBody` for POST/PUT is a JSON string (or `null` for an empty body).
`$apiKey` may be `null` to send an unauthenticated request.

**Example -- fetch the current user:**
```php
$r = Sillysite::get("http://localhost:8000", "mytoken123", "/whoami");
if ($r->status === 200) {
    echo $r->body . "\n";
} else {
    fwrite(STDERR, "HTTP " . $r->status . ": " . ($r->error ?? $r->body) . "\n");
}
```

**Example -- create a user:**
```php
$body = json_encode(["username" => "alice", "full_name" => "Alice Example", "password" => "s3cret"]);
$r = Sillysite::post("http://localhost:8000", "adminkey", "/users", $body);
if ($r->status === 201) echo "Created: " . $r->body . "\n";
```

---

## Programs

### `login.php`

```
./login.php <baseurl> <username>
```

Prompts for the password (masked via `stty -echo` when run in a real
terminal -- there's no built-in no-echo console read in PHP, so shelling
out to `stty` is the standard approach; read as a plain line otherwise,
the same fallback `../js/login.js` uses, unlike the C client, which
requires a real terminal/pty), performs the challenge/response login, and
prints the session token to stdout -- one line, no decoration. Mirrors
`../login.py`, `../c/login.c`, `../js/login.js`, `../java/Login.java`, and
`../csharp/Login.cs`.

```
$ ./login.php http://localhost:8000 alice
Password:
9a3f1b…
```

### `changepw.php`

```
./changepw.php <baseurl> <username>
```

Prompts for the current password, a new password, and a confirmation.
Verifies the two new-password entries match before proceeding. Mirrors
`../changepw.py`, `../c/changepw.c`, `../js/changepw.js`,
`../java/ChangePw.java`, and `../csharp/ChangePw.cs`.

```
$ ./changepw.php http://localhost:8000 alice
Current password:
New password:
Confirm new password:
Password changed successfully
```

Both scripts exit with status 1 and print a diagnostic to stderr on
error (wrong password, unknown user, network failure, etc.).
