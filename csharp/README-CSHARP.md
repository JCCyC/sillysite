# SillySite C# client library

A C# library (`Sillysite`) and two command-line programs that interact with
the SillySite API, built against Mono rather than the modern `dotnet` SDK.

## Prerequisites

```
sudo apt-get install mono-complete
```

Confirmed to install cleanly, with no extra repository (no Mono Project
PPA, no third-party apt source) on:
- Debian 12 ("bookworm", this project's dev container) — `mono-complete`
  6.8.0.105 from the `main` component.
- Ubuntu 22.04 ("jammy", Linux Mint 21.x's base) — the same upstream
  `mono-complete` 6.8.0.105, from the `universe` component (enabled by
  default).

Both resolve to the same upstream Mono release, just with different distro
packaging revisions/patch levels — there's no need to add
`download.mono-project.com` or any other third-party repository.

No other dependencies: the library uses only the BCL's
`System.Net.Http.HttpClient` and `System.Security.Cryptography`
(PBKDF2/HMAC) — no NuGet packages, no `dotnet` SDK, no `.csproj`/MSBuild.

## Building

```
cd csharp/
make
```

This produces `Sillysite.dll`, `Login.exe`, and `ChangePw.exe` in the same
directory (via `mcs`, Mono's C# compiler). Two wrapper scripts, `login` and
`changepw`, are checked in directly (not built) so the compiled client can
be invoked the same way as the C client's compiled binaries:

```
./login <baseurl> <username>
./changepw <baseurl> <username>
```

(equivalent to `mono Login.exe <baseurl> <username>` / `mono ChangePw.exe <baseurl> <username>`.)

---

## Library API (`Sillysite.cs`)

`Sillysite` has no namespace (mirroring `java/Sillysite.java`'s lack of a
package declaration) -- it's visible with no `using` directive needed,
from anything compiled or referenced alongside it.

### Response type

```csharp
public sealed class Response
{
    public readonly int Status;    // HTTP status code, or 0 on transport error
    public readonly string Body;   // response body, or null
    public readonly string Error;  // transport error description, or null
}
```

`Status == 0` means a transport-level failure (no HTTP response was
received); `Error` describes it. Otherwise `Status` is the real HTTP status
code and `Error` is `null`.

### SillyException

The high-level auth methods below throw `Sillysite.SillyException` on
failure, carrying the HTTP `Status` and response `Body` alongside the
message:

```csharp
public sealed class SillyException : Exception
{
    public readonly int Status;
    public readonly string Body;
}
```

---

### High-level auth methods

#### `Login`

```csharp
public static string Login(string baseUrl, string username, char[] password)
```

Performs the full challenge/response login flow and returns the session
token. The password is used locally to derive a PBKDF2-HMAC-SHA256 key and
then an HMAC-SHA256 response; the plaintext password is never sent over the
network. Passwords are `char[]` rather than `string` so callers can wipe
them (`Array.Clear(password, 0, password.Length)`) once done -- a `string`
can't be reliably zeroed since strings are immutable in .NET.

**Example:**
```csharp
char[] password = "s3cret".ToCharArray();
try
{
    string token = Sillysite.Login("http://localhost:8000", "alice", password);
    // use token ...
}
catch (Sillysite.SillyException e)
{
    Console.Error.WriteLine("login failed: " + e.Message);
}
finally
{
    Array.Clear(password, 0, password.Length);
}
```

---

#### `ChangePw`

```csharp
public static void ChangePw(string baseUrl, string username, char[] oldPassword, char[] newPassword)
```

Changes the user's password. Internally logs in with `oldPassword` to get a
session token, derives a fresh PBKDF2 salt/hash from `newPassword` locally,
and posts the derived values to `/change-password`. The new password is
never sent over the network.

---

#### `Logout`

```csharp
public static string Logout(string baseUrl, string apiKey)
```

Invalidates the session identified by `apiKey`. Returns the server's
confirmation message (e.g. `"User alice logged out"`). Throws if called
with the static `.env` `API_KEY`, which has no session to invalidate.

---

### Raw HTTP helpers

All four helpers construct the URL as `baseUrl + path`, send the request
with an optional `X-API-Key` header, and never throw -- transport failures
are reported through the returned `Response` (`Status = 0`, `Error` set),
the same as an ordinary HTTP error response.

```csharp
public static Response Get(string baseUrl, string apiKey, string path)
public static Response Post(string baseUrl, string apiKey, string path, string jsonBody)
public static Response Put(string baseUrl, string apiKey, string path, string jsonBody)
public static Response Delete(string baseUrl, string apiKey, string path)
```

`jsonBody` for POST/PUT is a JSON string (or `null` for an empty body).
`apiKey` may be `null` to send an unauthenticated request.

**Example -- fetch the current user:**
```csharp
Sillysite.Response r = Sillysite.Get("http://localhost:8000", "mytoken123", "/whoami");
if (r.Status == 200)
{
    Console.WriteLine(r.Body);
}
else
{
    Console.Error.WriteLine("HTTP " + r.Status + ": " + (r.Error ?? r.Body));
}
```

**Example -- create a user:**
```csharp
string body = "{\"username\":\"alice\",\"full_name\":\"Alice Example\",\"password\":\"s3cret\"}";
Sillysite.Response r = Sillysite.Post("http://localhost:8000", "adminkey", "/users", body);
if (r.Status == 201) Console.WriteLine("Created: " + r.Body);
```

---

## Programs

### `login` / `Login.exe`

```
./login <baseurl> <username>
```

Prompts for the password, performs the challenge/response login, and
prints the session token to stdout -- one line, no decoration. Mirrors
`../login.py`, `../c/login.c`, `../js/login.js`, and `../java/Login.java`.

When run in a real terminal, input is masked with `*` characters as you
type (the BCL has no built-in no-echo console read like Java's
`Console.readPassword()` or C's termios handling, so per-keystroke `*`
masking via `Console.ReadKey` is the standard fallback). When stdin is
piped/redirected, it's read as a plain line instead, the same fallback
`../js/login.js` uses (unlike the C client, which requires a real
terminal/pty).

```
$ ./login http://localhost:8000 alice
Password: ******
9a3f1b…
```

### `changepw` / `ChangePw.exe`

```
./changepw <baseurl> <username>
```

Prompts for the current password, a new password, and a confirmation.
Verifies the two new-password entries match before proceeding. Mirrors
`../changepw.py`, `../c/changepw.c`, `../js/changepw.js`, and
`../java/ChangePw.java`.

```
$ ./changepw http://localhost:8000 alice
Current password: ******
New password: ******
Confirm new password: ******
Password changed successfully
```

Both programs exit with status 1 and print a diagnostic to stderr on
error (wrong password, unknown user, network failure, etc.).
