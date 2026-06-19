# SillySite C client library

A C library (`libsillysite`) and two command-line programs that interact
with the SillySite API.

## Prerequisites

```
sudo apt-get install libcurl4-openssl-dev libcjson-dev
```

OpenSSL (`libssl-dev`) must also be present (it usually is).

## Building

```
cd c/
make
```

This produces `libsillysite.a` and the two programs `login` and `changepw`
in the same directory.

---

## Library API (`sillysite.h`)

Link with: `-lsillysite -lcurl -lssl -lcrypto -lcjson -lpthread`

### Response type

```c
typedef struct silly_response {
    int   status;   /* HTTP status code, or 0 on transport error */
    char *body;     /* NUL-terminated response body, or NULL     */
    char *error;    /* Human-readable error string, or NULL      */
} silly_response_t;

void silly_response_free(silly_response_t *r);
```

Always free responses with `silly_response_free()`. Never free individual
members or the struct directly.

`status == 0` means a transport-level failure (no HTTP response was
received); `error` will describe it. `status >= 100` is an HTTP response.

### errno

Every function sets `errno` on both success and failure:

| errno | Meaning |
|-------|---------|
| `0` | Success (2xx HTTP status) |
| `EACCES` | 401 or 403 — authentication or authorisation failure |
| `ENOENT` | 404 — resource not found |
| `EEXIST` | 409 — conflict (e.g. duplicate username) |
| `ETIMEDOUT` | Connect or response timed out |
| `ECONNREFUSED` | Server not reachable |
| `EHOSTUNREACH` | Hostname did not resolve |
| `ENOMEM` | Allocation failure |
| `EINVAL` | Bad arguments or malformed server response |
| `EIO` | Other / unexpected error |

---

### High-level auth functions

#### `silly_login`

```c
char *silly_login(const char *baseurl, const char *username,
                  const char *password);
```

Performs the full challenge/response login flow and returns a
heap-allocated NUL-terminated session token. The caller must `free()` it.

Returns `NULL` on failure with `errno` set.

The password is used locally to derive a PBKDF2-HMAC-SHA256 key and then
an HMAC-SHA256 response; the plaintext password is never sent over the
network.

**Example:**
```c
char *token = silly_login("http://localhost:8000", "alice", "s3cret");
if (!token) {
    fprintf(stderr, "login failed: %s\n", strerror(errno));
    exit(1);
}
/* use token … */
free(token);
```

---

#### `silly_changepw`

```c
int silly_changepw(const char *baseurl, const char *username,
                   const char *oldpw, const char *newpw);
```

Changes the user's password. Internally logs in with `oldpw` to get a
session token, derives a fresh PBKDF2 salt/hash from `newpw` locally, and
posts the derived values to `/change-password`. The new password is never
sent over the network.

Returns `0` on success, `-1` on failure with `errno` set.

---

#### `silly_logout`

```c
int silly_logout(const char *baseurl, const char *apikey);
```

Invalidates the session identified by `apikey`. Returns `0` on success,
`-1` on failure. Fails with `errno = EINVAL` / HTTP 400 if called with the
static `.env` `API_KEY` (which has no session to invalidate).

---

### Raw HTTP helpers

All four helpers construct the URL as `baseurl + path`, send the request
with an optional `X-API-Key` header, and return a heap-allocated
`silly_response_t` (free with `silly_response_free()`).

They return `NULL` (with `errno = ENOMEM`) only if the response struct
itself cannot be allocated. All other outcomes — including transport errors
— are returned through the struct (`status = 0`, `error` set).

#### `silly_get`

```c
silly_response_t *silly_get(const char *baseurl, const char *apikey,
                             const char *path);
```

#### `silly_post`

```c
silly_response_t *silly_post(const char *baseurl, const char *apikey,
                              const char *path, const char *body);
```

#### `silly_put`

```c
silly_response_t *silly_put(const char *baseurl, const char *apikey,
                             const char *path, const char *body);
```

#### `silly_delete`

```c
silly_response_t *silly_delete(const char *baseurl, const char *apikey,
                                const char *path);
```

`body` for POST/PUT is a JSON string (or `NULL` for an empty body).
`apikey` may be `NULL` to send an unauthenticated request.

**Example — fetch the current user:**
```c
silly_response_t *r = silly_get("http://localhost:8000",
                                 "mytoken123", "/whoami");
if (!r) { perror("silly_get"); exit(1); }

if (r->status == 200) {
    printf("%s\n", r->body);
} else {
    fprintf(stderr, "HTTP %d: %s\n", r->status,
            r->error ? r->error : r->body);
}
silly_response_free(r);
```

**Example — create a user:**
```c
const char *body = "{\"username\":\"alice\","
                   "\"full_name\":\"Alice Example\","
                   "\"password\":\"s3cret\"}";
silly_response_t *r = silly_post("http://localhost:8000",
                                  "adminkey", "/users", body);
if (r && r->status == 201)
    printf("Created: %s\n", r->body);
silly_response_free(r);
```

---

## Programs

### `login`

```
./login <baseurl> <username>
```

Prompts for the password on `/dev/tty` (with echo disabled), performs the
challenge/response login, and prints the session token to stdout — one line,
no decoration. Mirrors `../login.py`.

```
$ ./login http://localhost:8000 alice
Password:
9a3f1b…
```

### `changepw`

```
./changepw <baseurl> <username>
```

Prompts for the current password, a new password, and a confirmation.
Verifies the two new-password entries match before proceeding. Mirrors
`../changepw.py`.

```
$ ./changepw http://localhost:8000 alice
Current password:
New password:
Confirm new password:
Password changed successfully
```
