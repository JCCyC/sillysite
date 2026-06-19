# SillySite JavaScript client library

A JavaScript library (`sillysite.js`) and three Node CLI scripts that interact
with the SillySite API. The library works unmodified in Node (via `require`)
and in the browser (via a plain `<script>` tag, exposing `window.SillySite`).

## Prerequisites

None — no `apt-get` packages, no `npm install`. The library has zero
dependencies: in Node it uses only the built-in `http`/`https`/`crypto`
modules; in the browser it uses only `fetch` and `crypto.subtle` (both
already used by `static/login.html`). The CLI scripts need a Node binary
on your `PATH` (tested against the system's installed Node 12 — `node
--version`).

## Running the CLI scripts

```
node login.js <baseurl> <username>
node logout.js <baseurl> <apikey>
node changepw.js <baseurl> <username>
```

or, since they're executable with a `#!/usr/bin/env node` shebang:

```
./login.js <baseurl> <username>
```

---

## Library API (`sillysite.js`)

In Node:
```js
const SillySite = require('./sillysite');
```

In the browser:
```html
<script src="/path/to/sillysite.js"></script>
<script>
  SillySite.login('https://example.com', 'alice', 'secret').then(...);
</script>
```

Every function returns a Promise. There are no synchronous variants — the
browser's `crypto.subtle` API is inherently async, so the Node implementation
is async too for a single consistent interface.

### Raw HTTP helpers

```js
SillySite.request(baseUrl, apiKey, method, path, jsonBody)
SillySite.get(baseUrl, apiKey, path)
SillySite.post(baseUrl, apiKey, path, body)
SillySite.put(baseUrl, apiKey, path, body)
SillySite.del(baseUrl, apiKey, path)
```

- `apiKey` may be `null`/`undefined` for an unauthenticated request.
- `body` (for `post`/`put`) is a plain JS object/array — it's JSON-encoded
  for you. Pass `null`/`undefined` for no body.
- These never reject. They always resolve to:
  ```js
  { status: number, body: string|null, error: string|null }
  ```
  `status` is the real HTTP status code, with `body` set and `error: null`.
  On a transport-level failure (DNS, connection refused, timeout), `status`
  is `0`, `body` is `null`, and `error` holds a description.

**Example — fetch the current user:**
```js
const resp = await SillySite.get('http://localhost:8000', 'mytoken123', '/whoami');
if (resp.status === 200) {
  console.log(JSON.parse(resp.body));
} else {
  console.error(`HTTP ${resp.status}: ${resp.error || resp.body}`);
}
```

**Example — create a user:**
```js
const resp = await SillySite.post('http://localhost:8000', 'adminkey', '/users', {
  username: 'alice',
  full_name: 'Alice Example',
  password: 's3cret',
});
if (resp.status === 201) console.log('Created:', resp.body);
```

### High-level auth functions

These throw a `SillySite.SillyError` (an `Error` subclass with `.status`
and `.body` properties) on failure, instead of returning a status code —
idiomatic for `async`/`await` and `try`/`catch`.

#### `login(baseUrl, username, password)`

```js
const token = await SillySite.login('http://localhost:8000', 'alice', 's3cret');
```

Performs the full challenge/response login flow and resolves to the session
token string. The password is used locally to derive a PBKDF2-HMAC-SHA256
key and then an HMAC-SHA256 response; the plaintext password is never sent
over the network.

#### `changepw(baseUrl, username, oldPassword, newPassword)`

```js
await SillySite.changepw('http://localhost:8000', 'alice', 'oldpw', 'newpw');
```

Logs in with `oldPassword` to get a session token, derives a fresh PBKDF2
salt/hash locally from `newPassword`, and submits those to
`/change-password`. The new password is never sent over the network.
Resolves with no value on success.

#### `logout(baseUrl, apiKey)`

```js
const msg = await SillySite.logout('http://localhost:8000', token);
```

Invalidates the session identified by `apiKey`. Resolves to the server's
confirmation message (e.g. `"User alice logged out"`). Throws if called
with the static `.env` `API_KEY`, which has no session to invalidate.

---

## Programs

### `login.js`

```
node login.js <baseurl> <username>
```

Prompts for the password (without echoing it back, when run in a real
terminal), performs the challenge/response login, and prints the session
token to stdout — one line, no decoration. Mirrors `../login.py` and
`../c/login.c`.

```
$ node login.js http://localhost:8000 alice
Password:
9a3f1b…
```

### `logout.js`

```
node logout.js <baseurl> <apikey>
```

Invalidates the given session token and prints the server's confirmation
message.

```
$ node logout.js http://localhost:8000 9a3f1b...
User alice logged out
```

### `changepw.js`

```
node changepw.js <baseurl> <username>
```

Prompts for the current password, a new password, and a confirmation.
Verifies the two new-password entries match before proceeding. Mirrors
`../changepw.py` and `../c/changepw.c`.

```
$ node changepw.js http://localhost:8000 alice
Current password:
New password:
Confirm new password:
Password changed successfully
```

All three scripts exit with status 1 and print a diagnostic to stderr on
error (wrong password, unknown user, network failure, etc.).

### A note on password prompts and piped input

Unlike the C client's `login`/`changepw` (which read from `/dev/tty` and
require an actual terminal), these scripts read from stdin directly and
work whether stdin is an interactive terminal (input is hidden as you type)
or a pipe (e.g. for scripted/automated use — input is simply read as plain
lines, with no masking since there's no terminal to mask on).
