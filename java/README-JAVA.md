# SillySite Java client library

A Java library (`Sillysite`) and two command-line programs that interact
with the SillySite API.

## Prerequisites

A JDK, version 11 or newer (for `java.net.http.HttpClient`) -- tested
against OpenJDK 17:

```
sudo apt-get install openjdk-17-jdk-headless
```

No other dependencies: the library uses only the JDK's built-in
`java.net.http.HttpClient` (HTTP) and `javax.crypto` (PBKDF2/HMAC) --
no Maven, no Gradle, no third-party JSON library.

## Building

```
cd java/
make
```

This produces `Sillysite.class`, `Readpass.class`, `Login.class`, and
`ChangePw.class` in the same directory. Two wrapper scripts, `login` and
`changepw`, are checked in directly (not built) so the compiled client can
be invoked the same way as the C client's compiled binaries:

```
./login <baseurl> <username>
./changepw <baseurl> <username>
```

(equivalent to `java -cp . Login <baseurl> <username>` / `java -cp . ChangePw <baseurl> <username>`.)

---

## Library API (`Sillysite.java`)

`Sillysite` has no package declaration, so it's visible with no `import`
to any other unnamed-package class on the same classpath -- compile/run
from the `java/` directory, or put it on your classpath directly.

### Response type

```java
public static final class Response {
    public final int status;   // HTTP status code, or 0 on transport error
    public final String body;  // response body, or null
    public final String error; // transport error description, or null
}
```

`status == 0` means a transport-level failure (no HTTP response was
received); `error` describes it. Otherwise `status` is the real HTTP status
code and `error` is `null`.

### SillyException

The high-level auth methods below throw `Sillysite.SillyException` (a
checked exception) on failure, carrying the HTTP `status` and response
`body` alongside the message:

```java
public static final class SillyException extends Exception {
    public final int status;
    public final String body;
}
```

---

### High-level auth methods

#### `login`

```java
public static String login(String baseUrl, String username, char[] password) throws SillyException
```

Performs the full challenge/response login flow and returns the session
token. The password is used locally to derive a PBKDF2-HMAC-SHA256 key and
then an HMAC-SHA256 response; the plaintext password is never sent over
the network. Passwords are `char[]` rather than `String` so callers can
wipe them (`Arrays.fill(password, '\0')`) once done, the same reason
`Console.readPassword()` returns `char[]`.

**Example:**
```java
char[] password = "s3cret".toCharArray();
try {
    String token = Sillysite.login("http://localhost:8000", "alice", password);
    // use token ...
} catch (Sillysite.SillyException e) {
    System.err.println("login failed: " + e.getMessage());
} finally {
    java.util.Arrays.fill(password, '\0');
}
```

---

#### `changepw`

```java
public static void changepw(String baseUrl, String username, char[] oldPassword, char[] newPassword) throws SillyException
```

Changes the user's password. Internally logs in with `oldPassword` to get
a session token, derives a fresh PBKDF2 salt/hash from `newPassword`
locally, and posts the derived values to `/change-password`. The new
password is never sent over the network.

---

#### `logout`

```java
public static String logout(String baseUrl, String apiKey) throws SillyException
```

Invalidates the session identified by `apiKey`. Returns the server's
confirmation message (e.g. `"User alice logged out"`). Throws if called
with the static `.env` `API_KEY`, which has no session to invalidate.

---

### Raw HTTP helpers

All four helpers construct the URL as `baseUrl + path`, send the request
with an optional `X-API-Key` header, and never throw -- transport failures
are reported through the returned `Response` (`status = 0`, `error` set),
the same as an ordinary HTTP error response.

```java
public static Response get(String baseUrl, String apiKey, String path)
public static Response post(String baseUrl, String apiKey, String path, String jsonBody)
public static Response put(String baseUrl, String apiKey, String path, String jsonBody)
public static Response delete(String baseUrl, String apiKey, String path)
```

`jsonBody` for POST/PUT is a JSON string (or `null` for an empty body).
`apiKey` may be `null` to send an unauthenticated request.

**Example -- fetch the current user:**
```java
Sillysite.Response r = Sillysite.get("http://localhost:8000", "mytoken123", "/whoami");
if (r.status == 200) {
    System.out.println(r.body);
} else {
    System.err.println("HTTP " + r.status + ": " + (r.error != null ? r.error : r.body));
}
```

**Example -- create a user:**
```java
String body = "{\"username\":\"alice\",\"full_name\":\"Alice Example\",\"password\":\"s3cret\"}";
Sillysite.Response r = Sillysite.post("http://localhost:8000", "adminkey", "/users", body);
if (r.status == 201) System.out.println("Created: " + r.body);
```

---

## Programs

### `login` / `Login`

```
./login <baseurl> <username>
```

Prompts for the password (masked when run in a real terminal, read as a
plain line otherwise -- same fallback as `../js/login.js`, unlike the C
client which requires a real terminal/pty), performs the challenge/response
login, and prints the session token to stdout -- one line, no decoration.
Mirrors `../login.py`, `../c/login.c`, and `../js/login.js`.

```
$ ./login http://localhost:8000 alice
Password:
9a3f1b…
```

### `changepw` / `ChangePw`

```
./changepw <baseurl> <username>
```

Prompts for the current password, a new password, and a confirmation.
Verifies the two new-password entries match before proceeding. Mirrors
`../changepw.py`, `../c/changepw.c`, and `../js/changepw.js`.

```
$ ./changepw http://localhost:8000 alice
Current password:
New password:
Confirm new password:
Password changed successfully
```

Both programs exit with status 1 and print a diagnostic to stderr on
error (wrong password, unknown user, network failure, etc.).
