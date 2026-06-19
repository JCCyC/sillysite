/*
 * SillySite API client library.
 *
 * Works unmodified in Node (CommonJS, via require) and in the browser
 * (via a plain <script> tag, exposing window.SillySite) — no dependencies,
 * no build step. Node support targets the http/https/crypto built-ins
 * (no global fetch or crypto.subtle assumed); browser support targets
 * fetch and crypto.subtle.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.SillySite = factory();
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var isNode = typeof process !== 'undefined' && !!(process.versions && process.versions.node);

  var nodeCrypto = isNode ? require('crypto') : null;
  var nodeHttp = isNode ? require('http') : null;
  var nodeHttps = isNode ? require('https') : null;

  var PBKDF2_ITERATIONS = 200000;
  var DERIVED_KEY_LEN = 32;
  var SALT_BYTES = 16;

  function SillyError(message, status, body) {
    Error.call(this, message);
    this.name = 'SillyError';
    this.message = message;
    this.status = status;
    this.body = body;
    if (Error.captureStackTrace) Error.captureStackTrace(this, SillyError);
  }
  SillyError.prototype = Object.create(Error.prototype);
  SillyError.prototype.constructor = SillyError;

  /* ------------------------------------------------------------------ */
  /* hex / byte helpers                                                  */
  /* ------------------------------------------------------------------ */

  function bytesToHex(bytes) {
    var hex = '';
    for (var i = 0; i < bytes.length; i++) {
      hex += ('0' + bytes[i].toString(16)).slice(-2);
    }
    return hex;
  }

  function hexToBytes(hex) {
    if (typeof hex !== 'string' || hex.length % 2 !== 0) {
      throw new SillyError('Invalid hex string from server', 0, null);
    }
    var bytes = new Uint8Array(hex.length / 2);
    for (var i = 0; i < bytes.length; i++) {
      bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
    }
    return bytes;
  }

  function utf8Bytes(str) {
    if (isNode) return new Uint8Array(Buffer.from(str, 'utf8'));
    return new TextEncoder().encode(str);
  }

  /* ------------------------------------------------------------------ */
  /* crypto: PBKDF2-HMAC-SHA256, HMAC-SHA256, random bytes               */
  /* ------------------------------------------------------------------ */

  function pbkdf2(passwordBytes, saltBytes, iterations, keylen) {
    if (isNode) {
      return new Promise(function (resolve, reject) {
        nodeCrypto.pbkdf2(
          Buffer.from(passwordBytes), Buffer.from(saltBytes), iterations, keylen, 'sha256',
          function (err, derived) {
            if (err) reject(err);
            else resolve(new Uint8Array(derived));
          }
        );
      });
    }
    return crypto.subtle.importKey('raw', passwordBytes, 'PBKDF2', false, ['deriveBits'])
      .then(function (keyMaterial) {
        return crypto.subtle.deriveBits(
          { name: 'PBKDF2', salt: saltBytes, iterations: iterations, hash: 'SHA-256' },
          keyMaterial,
          keylen * 8
        );
      })
      .then(function (bits) { return new Uint8Array(bits); });
  }

  function hmacSha256(keyBytes, msgBytes) {
    if (isNode) {
      var h = nodeCrypto.createHmac('sha256', Buffer.from(keyBytes));
      h.update(Buffer.from(msgBytes));
      return Promise.resolve(new Uint8Array(h.digest()));
    }
    return crypto.subtle.importKey('raw', keyBytes, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
      .then(function (key) { return crypto.subtle.sign('HMAC', key, msgBytes); })
      .then(function (sig) { return new Uint8Array(sig); });
  }

  function randomBytes(n) {
    if (isNode) return new Uint8Array(nodeCrypto.randomBytes(n));
    var b = new Uint8Array(n);
    crypto.getRandomValues(b);
    return b;
  }

  /* ------------------------------------------------------------------ */
  /* HTTP transport                                                       */
  /* ------------------------------------------------------------------ */

  function buildUrl(baseUrl, path) {
    var trimmedBase = baseUrl.replace(/\/+$/, '');
    var sep = path.charAt(0) === '/' ? '' : '/';
    return trimmedBase + sep + path;
  }

  function nodeRequest(url, apiKey, method, bodyStr) {
    return new Promise(function (resolve) {
      var parsed;
      try {
        parsed = new URL(url);
      } catch (err) {
        resolve({ status: 0, body: null, error: err.message });
        return;
      }
      var transport = parsed.protocol === 'https:' ? nodeHttps : nodeHttp;

      var headers = { 'Content-Type': 'application/json' };
      if (apiKey) headers['X-API-Key'] = apiKey;
      var bodyBuf = bodyStr ? Buffer.from(bodyStr, 'utf8') : null;
      if (bodyBuf) headers['Content-Length'] = bodyBuf.length;

      var options = {
        hostname: parsed.hostname,
        path: parsed.pathname + (parsed.search || ''),
        method: method,
        headers: headers,
      };
      if (parsed.port) options.port = parsed.port;

      var req = transport.request(options, function (res) {
        var chunks = [];
        res.on('data', function (chunk) { chunks.push(chunk); });
        res.on('end', function () {
          resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString('utf8'), error: null });
        });
      });

      req.on('error', function (err) {
        resolve({ status: 0, body: null, error: err.message });
      });

      if (bodyBuf) req.write(bodyBuf);
      req.end();
    });
  }

  function browserRequest(url, apiKey, method, bodyStr) {
    var headers = { 'Content-Type': 'application/json' };
    if (apiKey) headers['X-API-Key'] = apiKey;
    return fetch(url, { method: method, headers: headers, body: bodyStr || undefined })
      .then(function (res) {
        return res.text().then(function (text) {
          return { status: res.status, body: text, error: null };
        });
      })
      .catch(function (err) {
        return { status: 0, body: null, error: err.message };
      });
  }

  /**
   * Low-level request. Never rejects: transport failures resolve with
   * status 0 and an `error` string, mirroring HTTP responses which
   * resolve with the actual status and `error: null`.
   *
   * @returns {Promise<{status: number, body: (string|null), error: (string|null)}>}
   */
  function request(baseUrl, apiKey, method, path, jsonBody) {
    var url = buildUrl(baseUrl, path);
    var bodyStr = (jsonBody !== undefined && jsonBody !== null) ? JSON.stringify(jsonBody) : null;
    return isNode
      ? nodeRequest(url, apiKey, method, bodyStr)
      : browserRequest(url, apiKey, method, bodyStr);
  }

  function get(baseUrl, apiKey, path) {
    return request(baseUrl, apiKey, 'GET', path);
  }

  function post(baseUrl, apiKey, path, body) {
    return request(baseUrl, apiKey, 'POST', path, body);
  }

  function put(baseUrl, apiKey, path, body) {
    return request(baseUrl, apiKey, 'PUT', path, body);
  }

  function del(baseUrl, apiKey, path) {
    return request(baseUrl, apiKey, 'DELETE', path);
  }

  /* ------------------------------------------------------------------ */
  /* High-level auth flows                                               */
  /* ------------------------------------------------------------------ */

  function errorMessageFromResponse(resp, fallback) {
    if (resp.body) {
      try {
        var data = JSON.parse(resp.body);
        if (data && typeof data.detail === 'string') return data.detail;
      } catch (e) { /* not JSON */ }
    }
    if (resp.error) return resp.error;
    return fallback;
  }

  function doLogin(baseUrl, username, password) {
    return post(baseUrl, null, '/login/challenge', { username: username })
      .then(function (challResp) {
        if (challResp.status !== 200) {
          throw new SillyError(
            errorMessageFromResponse(challResp, 'Failed to obtain login challenge'),
            challResp.status, challResp.body
          );
        }
        var challengeData = JSON.parse(challResp.body);
        var saltBytes = hexToBytes(challengeData.salt);
        var challengeBytes = hexToBytes(challengeData.challenge);

        return pbkdf2(utf8Bytes(password), saltBytes, challengeData.iterations, DERIVED_KEY_LEN)
          .then(function (derivedKey) { return hmacSha256(derivedKey, challengeBytes); })
          .then(function (hmacOut) {
            return post(baseUrl, null, '/login/response', {
              username: username,
              challenge: challengeData.challenge,
              response: bytesToHex(hmacOut),
            });
          });
      })
      .then(function (loginResp) {
        if (loginResp.status !== 200) {
          throw new SillyError(
            errorMessageFromResponse(loginResp, 'Invalid username or password'),
            loginResp.status, loginResp.body
          );
        }
        return JSON.parse(loginResp.body).token;
      });
  }

  /**
   * Performs the challenge/response login flow.
   * @returns {Promise<string>} the session token
   */
  function login(baseUrl, username, password) {
    if (!baseUrl || !username || !password) {
      return Promise.reject(new SillyError('baseUrl, username, and password are required', 0, null));
    }
    return doLogin(baseUrl, username, password);
  }

  /**
   * Logs in with oldPassword, then derives fresh credentials from
   * newPassword locally and submits them — newPassword is never sent
   * over the network.
   * @returns {Promise<void>}
   */
  function changepw(baseUrl, username, oldPassword, newPassword) {
    if (!baseUrl || !username || !oldPassword || !newPassword) {
      return Promise.reject(new SillyError('baseUrl, username, oldPassword, and newPassword are required', 0, null));
    }
    return doLogin(baseUrl, username, oldPassword)
      .then(function (token) {
        var newSalt = randomBytes(SALT_BYTES);
        return pbkdf2(utf8Bytes(newPassword), newSalt, PBKDF2_ITERATIONS, DERIVED_KEY_LEN)
          .then(function (newHash) {
            return post(baseUrl, token, '/change-password', {
              new_salt: bytesToHex(newSalt),
              new_password_hash: bytesToHex(newHash),
              new_iterations: PBKDF2_ITERATIONS,
            });
          });
      })
      .then(function (resp) {
        if (resp.status !== 200 && resp.status !== 204) {
          throw new SillyError(errorMessageFromResponse(resp, 'Change password failed'), resp.status, resp.body);
        }
      });
  }

  /**
   * Invalidates the session identified by apiKey.
   * @returns {Promise<string|undefined>} the server's confirmation message, if any
   */
  function logout(baseUrl, apiKey) {
    if (!baseUrl || !apiKey) {
      return Promise.reject(new SillyError('baseUrl and apiKey are required', 0, null));
    }
    return get(baseUrl, apiKey, '/logout').then(function (resp) {
      if (resp.status !== 200) {
        throw new SillyError(errorMessageFromResponse(resp, 'Logout failed'), resp.status, resp.body);
      }
      try {
        return JSON.parse(resp.body).msg;
      } catch (e) {
        return undefined;
      }
    });
  }

  return {
    request: request,
    get: get,
    post: post,
    put: put,
    del: del,
    login: login,
    changepw: changepw,
    logout: logout,
    SillyError: SillyError,
  };
});
