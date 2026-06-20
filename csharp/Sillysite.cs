using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;

/// <summary>
/// SillySite API client library.
///
/// Uses only the BCL's <see cref="HttpClient"/> and
/// <see cref="System.Security.Cryptography"/> (PBKDF2/HMAC) -- no external
/// dependencies, no NuGet packages, mirroring the zero-dependency design of
/// <c>js/sillysite.js</c> and <c>java/Sillysite.java</c>. No namespace, for
/// the same reason <c>java/Sillysite.java</c> has no package: this is the
/// only type consumers need, visible with no <c>using</c> directive needed.
/// </summary>
public static class Sillysite
{
    private const int Pbkdf2Iterations = 200_000;
    private const int DerivedKeyLen = 32;
    private const int SaltBytes = 16;

    private static readonly HttpClient HttpClientInstance = new HttpClient
    {
        Timeout = TimeSpan.FromSeconds(30),
    };

    /// <summary>Result of a raw HTTP call -- see <see cref="Get"/> / <see cref="Post"/> / <see cref="Put"/> / <see cref="Delete"/>.</summary>
    public sealed class Response
    {
        /// <summary>HTTP status code, or 0 on a transport-level failure (DNS, connection refused, timeout, ...).</summary>
        public readonly int Status;
        /// <summary>Response body, or null if none was received.</summary>
        public readonly string Body;
        /// <summary>Human-readable transport error, or null if an HTTP response was received.</summary>
        public readonly string Error;

        internal Response(int status, string body, string error)
        {
            Status = status;
            Body = body;
            Error = error;
        }
    }

    /// <summary>Thrown by the high-level auth methods (<see cref="Login"/>, <see cref="ChangePw"/>, <see cref="Logout"/>) on failure.</summary>
    public sealed class SillyException : Exception
    {
        /// <summary>HTTP status code, or 0 if the failure was a transport error or an argument check.</summary>
        public readonly int Status;
        /// <summary>Response body, if any.</summary>
        public readonly string Body;

        public SillyException(string message, int status, string body) : base(message)
        {
            Status = status;
            Body = body;
        }
    }

    /* ------------------------------------------------------------------ */
    /* Raw HTTP helpers                                                    */
    /* ------------------------------------------------------------------ */

    /// <summary>
    /// GET baseUrl+path, optionally authenticated with apiKey (sent as
    /// X-API-Key; pass null to omit). Never throws: transport failures are
    /// reported through the returned Response (status 0, error set), the
    /// same as an ordinary HTTP error response.
    /// </summary>
    public static Response Get(string baseUrl, string apiKey, string path)
    {
        return RequestAsync(baseUrl, apiKey, HttpMethod.Get, path, null).GetAwaiter().GetResult();
    }

    /// <summary>POST baseUrl+path with a JSON request body (pass null for an empty body).</summary>
    public static Response Post(string baseUrl, string apiKey, string path, string jsonBody)
    {
        return RequestAsync(baseUrl, apiKey, HttpMethod.Post, path, jsonBody).GetAwaiter().GetResult();
    }

    /// <summary>PUT baseUrl+path with a JSON request body (pass null for an empty body).</summary>
    public static Response Put(string baseUrl, string apiKey, string path, string jsonBody)
    {
        return RequestAsync(baseUrl, apiKey, HttpMethod.Put, path, jsonBody).GetAwaiter().GetResult();
    }

    /// <summary>DELETE baseUrl+path.</summary>
    public static Response Delete(string baseUrl, string apiKey, string path)
    {
        return RequestAsync(baseUrl, apiKey, HttpMethod.Delete, path, null).GetAwaiter().GetResult();
    }

    private static async Task<Response> RequestAsync(
        string baseUrl, string apiKey, HttpMethod method, string path, string jsonBody)
    {
        Uri uri;
        try
        {
            uri = new Uri(BuildUrl(baseUrl, path));
        }
        catch (Exception e)
        {
            return new Response(0, null, e.Message);
        }

        using (var request = new HttpRequestMessage(method, uri))
        {
            if (apiKey != null)
            {
                request.Headers.Add("X-API-Key", apiKey);
            }
            // Always attach Content (even empty) for POST/PUT, matching
            // js/sillysite.js and c/sillysite.c, which both still send a
            // Content-Type header on a bodyless POST/PUT.
            if (jsonBody != null || method == HttpMethod.Post || method == HttpMethod.Put)
            {
                request.Content = new StringContent(jsonBody ?? string.Empty, Encoding.UTF8, "application/json");
            }

            try
            {
                using (var response = await HttpClientInstance.SendAsync(request).ConfigureAwait(false))
                {
                    string body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                    return new Response((int)response.StatusCode, body, null);
                }
            }
            catch (Exception e)
            {
                return new Response(0, null, e.Message);
            }
        }
    }

    private static string BuildUrl(string baseUrl, string path)
    {
        string trimmed = baseUrl.TrimEnd('/');
        string sep = (path.Length > 0 && path[0] == '/') ? string.Empty : "/";
        return trimmed + sep + path;
    }

    private static string ErrorMessage(Response resp, string fallback)
    {
        if (resp.Body != null)
        {
            try
            {
                string detail;
                if (Json.ParseObject(resp.Body).TryGetValue("detail", out detail))
                {
                    return detail;
                }
            }
            catch (FormatException)
            {
                // not JSON
            }
        }
        return resp.Error ?? fallback;
    }

    /* ------------------------------------------------------------------ */
    /* High-level auth flows                                               */
    /* ------------------------------------------------------------------ */

    /// <summary>Performs the challenge/response login flow. Returns the session token.</summary>
    public static string Login(string baseUrl, string username, char[] password)
    {
        if (baseUrl == null || username == null || password == null)
        {
            throw new SillyException("baseUrl, username, and password are required", 0, null);
        }
        return DoLogin(baseUrl, username, password);
    }

    private static string DoLogin(string baseUrl, string username, char[] password)
    {
        Response challResp = Post(baseUrl, null, "/login/challenge", Json.Object("username", username));
        if (challResp.Status != 200)
        {
            throw new SillyException(
                ErrorMessage(challResp, "Failed to obtain login challenge"), challResp.Status, challResp.Body);
        }
        Dictionary<string, string> challengeData = Json.ParseObject(challResp.Body);
        byte[] saltBytes = HexToBytes(challengeData["salt"]);
        byte[] challengeBytes = HexToBytes(challengeData["challenge"]);
        int iterations = int.Parse(challengeData["iterations"]);

        byte[] derivedKey = Pbkdf2(password, saltBytes, iterations, DerivedKeyLen);
        byte[] hmacOut = HmacSha256(derivedKey, challengeBytes);

        Response loginResp = Post(baseUrl, null, "/login/response", Json.Object(
            "username", username,
            "challenge", challengeData["challenge"],
            "response", BytesToHex(hmacOut)));
        if (loginResp.Status != 200)
        {
            throw new SillyException(
                ErrorMessage(loginResp, "Invalid username or password"), loginResp.Status, loginResp.Body);
        }
        return Json.ParseObject(loginResp.Body)["token"];
    }

    /// <summary>
    /// Logs in with oldPassword, then derives fresh credentials from
    /// newPassword locally and submits them -- newPassword is never sent
    /// over the network.
    /// </summary>
    public static void ChangePw(string baseUrl, string username, char[] oldPassword, char[] newPassword)
    {
        if (baseUrl == null || username == null || oldPassword == null || newPassword == null)
        {
            throw new SillyException("baseUrl, username, oldPassword, and newPassword are required", 0, null);
        }
        string token = DoLogin(baseUrl, username, oldPassword);

        byte[] newSalt = RandomBytes(SaltBytes);
        byte[] newHash = Pbkdf2(newPassword, newSalt, Pbkdf2Iterations, DerivedKeyLen);

        Response resp = Post(baseUrl, token, "/change-password", Json.Object(
            "new_salt", BytesToHex(newSalt),
            "new_password_hash", BytesToHex(newHash),
            "new_iterations", Pbkdf2Iterations));
        if (resp.Status != 200 && resp.Status != 204)
        {
            throw new SillyException(ErrorMessage(resp, "Change password failed"), resp.Status, resp.Body);
        }
    }

    /// <summary>Invalidates the session identified by apiKey. Returns the server's confirmation message, or null if the response had none.</summary>
    public static string Logout(string baseUrl, string apiKey)
    {
        if (baseUrl == null || apiKey == null)
        {
            throw new SillyException("baseUrl and apiKey are required", 0, null);
        }
        Response resp = Get(baseUrl, apiKey, "/logout");
        if (resp.Status != 200)
        {
            throw new SillyException(ErrorMessage(resp, "Logout failed"), resp.Status, resp.Body);
        }
        try
        {
            string msg;
            Json.ParseObject(resp.Body).TryGetValue("msg", out msg);
            return msg;
        }
        catch (FormatException)
        {
            return null;
        }
    }

    /* ------------------------------------------------------------------ */
    /* Crypto: PBKDF2-HMAC-SHA256, HMAC-SHA256, random bytes               */
    /* ------------------------------------------------------------------ */

    /// <summary>
    /// Converts the password to UTF-8 bytes ourselves (rather than using
    /// the string-accepting Rfc2898DeriveBytes constructor) for two
    /// reasons: it matches Python's hashlib.pbkdf2_hmac/Node's
    /// crypto.pbkdf2/OpenSSL's PKCS5_PBKDF2_HMAC/Java's
    /// PBKDF2WithHmacSHA256 byte-for-byte (confirmed by hand against a
    /// password containing accented Latin, currency, and CJK characters --
    /// the string overload is documented to do the same UTF-8 encoding
    /// internally, so this isn't strictly required for correctness here,
    /// only for the second reason); and it lets the intermediate byte[] be
    /// explicitly cleared afterward, the same as the char[] password
    /// itself -- a string copy of the password would otherwise linger in
    /// memory with no way to wipe it.
    /// </summary>
    private static byte[] Pbkdf2(char[] password, byte[] salt, int iterations, int keyLenBytes)
    {
        byte[] passwordUtf8 = Encoding.UTF8.GetBytes(password);
        try
        {
            using (var pbkdf2 = new Rfc2898DeriveBytes(passwordUtf8, salt, iterations, HashAlgorithmName.SHA256))
            {
                return pbkdf2.GetBytes(keyLenBytes);
            }
        }
        finally
        {
            Array.Clear(passwordUtf8, 0, passwordUtf8.Length);
        }
    }

    private static byte[] HmacSha256(byte[] key, byte[] message)
    {
        using (var hmac = new HMACSHA256(key))
        {
            return hmac.ComputeHash(message);
        }
    }

    private static byte[] RandomBytes(int n)
    {
        byte[] b = new byte[n];
        using (var rng = RandomNumberGenerator.Create())
        {
            rng.GetBytes(b);
        }
        return b;
    }

    /* ------------------------------------------------------------------ */
    /* hex / byte helpers                                                  */
    /* ------------------------------------------------------------------ */

    private static string BytesToHex(byte[] bytes)
    {
        var sb = new StringBuilder(bytes.Length * 2);
        foreach (byte b in bytes)
        {
            sb.Append(b.ToString("x2"));
        }
        return sb.ToString();
    }

    private static byte[] HexToBytes(string hex)
    {
        if (hex == null || hex.Length % 2 != 0)
        {
            throw new SillyException("Invalid hex string from server", 0, null);
        }
        byte[] result = new byte[hex.Length / 2];
        for (int i = 0; i < result.Length; i++)
        {
            int hi = HexDigit(hex[i * 2]);
            int lo = HexDigit(hex[i * 2 + 1]);
            if (hi < 0 || lo < 0)
            {
                throw new SillyException("Invalid hex string from server", 0, null);
            }
            result[i] = (byte)((hi << 4) | lo);
        }
        return result;
    }

    private static int HexDigit(char c)
    {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        return -1;
    }

    /* ------------------------------------------------------------------ */
    /* Minimal JSON encode/decode for this API's flat request/response     */
    /* shapes only -- no nested objects/arrays, since none of the          */
    /* endpoints used here ever produce or expect any.                     */
    /* ------------------------------------------------------------------ */

    private static class Json
    {
        /// <summary>Builds a flat {"k":"v",...} object. Values are string (quoted+escaped) or int (bare).</summary>
        public static string Object(params object[] kv)
        {
            var sb = new StringBuilder("{");
            for (int i = 0; i < kv.Length; i += 2)
            {
                if (i > 0)
                {
                    sb.Append(',');
                }
                sb.Append('"').Append(kv[i]).Append("\":");
                object value = kv[i + 1];
                if (value is int || value is long)
                {
                    sb.Append(value);
                }
                else
                {
                    sb.Append('"').Append(Escape(Convert.ToString(value))).Append('"');
                }
            }
            return sb.Append('}').ToString();
        }

        private static string Escape(string s)
        {
            var sb = new StringBuilder(s.Length);
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20)
                        {
                            sb.Append("\\u").Append(((int)c).ToString("x4"));
                        }
                        else
                        {
                            sb.Append(c);
                        }
                        break;
                }
            }
            return sb.ToString();
        }

        /// <summary>
        /// Parses a single-level JSON object into a key -&gt; raw-value map.
        /// String values are unescaped; numbers/literals are kept as their
        /// literal text (callers that need an int call int.Parse on the
        /// result).
        /// </summary>
        public static Dictionary<string, string> ParseObject(string json)
        {
            if (json == null)
            {
                throw new FormatException("null body");
            }
            int pos = SkipWs(json, 0);
            Expect(json, ref pos, '{');
            var map = new Dictionary<string, string>();
            pos = SkipWs(json, pos);
            if (Peek(json, pos) == '}')
            {
                return map;
            }
            while (true)
            {
                pos = SkipWs(json, pos);
                string key = ParseString(json, ref pos);
                pos = SkipWs(json, pos);
                Expect(json, ref pos, ':');
                pos = SkipWs(json, pos);
                string value = (Peek(json, pos) == '"') ? ParseString(json, ref pos) : ParseLiteral(json, ref pos);
                map[key] = value;
                pos = SkipWs(json, pos);
                char c = Peek(json, pos);
                pos++;
                if (c == ',') continue;
                if (c == '}') break;
                throw new FormatException("malformed JSON object at " + pos);
            }
            return map;
        }

        private static string ParseString(string json, ref int pos)
        {
            Expect(json, ref pos, '"');
            var sb = new StringBuilder();
            while (true)
            {
                char c = Peek(json, pos);
                pos++;
                if (c == '"')
                {
                    return sb.ToString();
                }
                if (c == '\\')
                {
                    char esc = Peek(json, pos);
                    pos++;
                    switch (esc)
                    {
                        case '"': sb.Append('"'); break;
                        case '\\': sb.Append('\\'); break;
                        case '/': sb.Append('/'); break;
                        case 'b': sb.Append('\b'); break;
                        case 'f': sb.Append('\f'); break;
                        case 'n': sb.Append('\n'); break;
                        case 'r': sb.Append('\r'); break;
                        case 't': sb.Append('\t'); break;
                        case 'u':
                            sb.Append((char)Convert.ToInt32(json.Substring(pos, 4), 16));
                            pos += 4;
                            break;
                        default:
                            throw new FormatException("bad escape at " + pos);
                    }
                }
                else
                {
                    sb.Append(c);
                }
            }
        }

        private static string ParseLiteral(string json, ref int pos)
        {
            int start = pos;
            while (pos < json.Length && ",}".IndexOf(json[pos]) < 0 && !char.IsWhiteSpace(json[pos]))
            {
                pos++;
            }
            return json.Substring(start, pos - start);
        }

        private static int SkipWs(string json, int i)
        {
            while (i < json.Length && char.IsWhiteSpace(json[i]))
            {
                i++;
            }
            return i;
        }

        private static char Peek(string json, int pos)
        {
            if (pos >= json.Length)
            {
                throw new FormatException("unexpected end of JSON");
            }
            return json[pos];
        }

        private static void Expect(string json, ref int pos, char c)
        {
            if (Peek(json, pos) != c)
            {
                throw new FormatException("expected '" + c + "' at " + pos);
            }
            pos++;
        }
    }
}
