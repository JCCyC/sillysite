import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.SecureRandom;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import javax.crypto.Mac;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;

/**
 * SillySite API client library.
 *
 * Uses only the JDK's built-in {@code java.net.http.HttpClient} and
 * {@code javax.crypto} (PBKDF2/HMAC) -- no external dependencies, no build
 * tool (Maven/Gradle), mirroring the zero-dependency design of {@code
 * js/sillysite.js} and the system-library-only design of {@code c/sillysite.c}.
 */
public final class Sillysite {
    private Sillysite() {}

    private static final int PBKDF2_ITERATIONS = 200_000;
    private static final int DERIVED_KEY_LEN = 32;
    private static final int SALT_BYTES = 16;

    // HTTP/1.1 explicitly: HttpClient's default HTTP/2-with-upgrade
    // negotiation silently drops the request body against this server
    // (uvicorn) -- confirmed by hand: an identical request succeeds with
    // .version(HTTP_1_1) and gets back a 422 "body: Field required" with
    // the default version, despite the client reporting the correct
    // Content-Length either way.
    private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    /** Result of a raw HTTP call -- see {@link #get} / {@link #post} / {@link #put} / {@link #delete}. */
    public static final class Response {
        /** HTTP status code, or 0 on a transport-level failure (DNS, connection refused, timeout, ...). */
        public final int status;
        /** Response body, or null if none was received. */
        public final String body;
        /** Human-readable transport error, or null if an HTTP response was received. */
        public final String error;

        Response(int status, String body, String error) {
            this.status = status;
            this.body = body;
            this.error = error;
        }
    }

    /** Thrown by the high-level auth methods ({@link #login}, {@link #changepw}, {@link #logout}) on failure. */
    public static final class SillyException extends Exception {
        /** HTTP status code, or 0 if the failure was a transport error or an argument check. */
        public final int status;
        /** Response body, if any. */
        public final String body;

        public SillyException(String message, int status, String body) {
            super(message);
            this.status = status;
            this.body = body;
        }
    }

    /* ------------------------------------------------------------------ */
    /* Raw HTTP helpers                                                    */
    /* ------------------------------------------------------------------ */

    /**
     * GET baseUrl+path, optionally authenticated with apiKey (sent as
     * X-API-Key; pass null to omit). Never throws: transport failures are
     * reported through the returned Response (status 0, error set), the
     * same as an ordinary HTTP error response.
     */
    public static Response get(String baseUrl, String apiKey, String path) {
        return request(baseUrl, apiKey, "GET", path, null);
    }

    /** POST baseUrl+path with a JSON request body (pass null for an empty body). */
    public static Response post(String baseUrl, String apiKey, String path, String jsonBody) {
        return request(baseUrl, apiKey, "POST", path, jsonBody);
    }

    /** PUT baseUrl+path with a JSON request body (pass null for an empty body). */
    public static Response put(String baseUrl, String apiKey, String path, String jsonBody) {
        return request(baseUrl, apiKey, "PUT", path, jsonBody);
    }

    /** DELETE baseUrl+path. */
    public static Response delete(String baseUrl, String apiKey, String path) {
        return request(baseUrl, apiKey, "DELETE", path, null);
    }

    private static Response request(String baseUrl, String apiKey, String method, String path, String jsonBody) {
        HttpRequest.Builder builder;
        try {
            builder = HttpRequest.newBuilder()
                    .uri(URI.create(buildUrl(baseUrl, path)))
                    .timeout(Duration.ofSeconds(30))
                    .header("Content-Type", "application/json");
        } catch (RuntimeException e) {
            return new Response(0, null, e.getMessage());
        }
        if (apiKey != null) {
            builder.header("X-API-Key", apiKey);
        }

        HttpRequest.BodyPublisher publisher = jsonBody != null
                ? HttpRequest.BodyPublishers.ofString(jsonBody, StandardCharsets.UTF_8)
                : HttpRequest.BodyPublishers.noBody();
        switch (method) {
            case "GET":
                builder.GET();
                break;
            case "POST":
                builder.POST(publisher);
                break;
            case "PUT":
                builder.PUT(publisher);
                break;
            case "DELETE":
                builder.DELETE();
                break;
            default:
                throw new IllegalArgumentException("unsupported method: " + method);
        }

        try {
            HttpResponse<String> resp = HTTP_CLIENT.send(builder.build(), HttpResponse.BodyHandlers.ofString());
            return new Response(resp.statusCode(), resp.body(), null);
        } catch (IOException | InterruptedException e) {
            return new Response(0, null, e.getMessage());
        }
    }

    private static String buildUrl(String baseUrl, String path) {
        String trimmed = baseUrl.replaceAll("/+$", "");
        String sep = (!path.isEmpty() && path.charAt(0) == '/') ? "" : "/";
        return trimmed + sep + path;
    }

    private static String errorMessage(Response resp, String fallback) {
        if (resp.body != null) {
            try {
                String detail = Json.parseObject(resp.body).get("detail");
                if (detail != null) {
                    return detail;
                }
            } catch (RuntimeException notJson) {
                // fall through
            }
        }
        return resp.error != null ? resp.error : fallback;
    }

    /* ------------------------------------------------------------------ */
    /* High-level auth flows                                               */
    /* ------------------------------------------------------------------ */

    /**
     * Performs the challenge/response login flow.
     *
     * @return the session token
     */
    public static String login(String baseUrl, String username, char[] password) throws SillyException {
        if (baseUrl == null || username == null || password == null) {
            throw new SillyException("baseUrl, username, and password are required", 0, null);
        }
        return doLogin(baseUrl, username, password);
    }

    private static String doLogin(String baseUrl, String username, char[] password) throws SillyException {
        Response challResp = post(baseUrl, null, "/login/challenge", Json.object("username", username));
        if (challResp.status != 200) {
            throw new SillyException(
                    errorMessage(challResp, "Failed to obtain login challenge"), challResp.status, challResp.body);
        }
        Map<String, String> challengeData = Json.parseObject(challResp.body);
        byte[] saltBytes = hexToBytes(challengeData.get("salt"));
        byte[] challengeBytes = hexToBytes(challengeData.get("challenge"));
        int iterations = Integer.parseInt(challengeData.get("iterations"));

        byte[] derivedKey = pbkdf2(password, saltBytes, iterations, DERIVED_KEY_LEN);
        byte[] hmacOut = hmacSha256(derivedKey, challengeBytes);

        Response loginResp = post(baseUrl, null, "/login/response", Json.object(
                "username", username,
                "challenge", challengeData.get("challenge"),
                "response", bytesToHex(hmacOut)));
        if (loginResp.status != 200) {
            throw new SillyException(
                    errorMessage(loginResp, "Invalid username or password"), loginResp.status, loginResp.body);
        }
        return Json.parseObject(loginResp.body).get("token");
    }

    /**
     * Logs in with oldPassword, then derives fresh credentials from
     * newPassword locally and submits them -- newPassword is never sent
     * over the network.
     */
    public static void changepw(String baseUrl, String username, char[] oldPassword, char[] newPassword)
            throws SillyException {
        if (baseUrl == null || username == null || oldPassword == null || newPassword == null) {
            throw new SillyException("baseUrl, username, oldPassword, and newPassword are required", 0, null);
        }
        String token = doLogin(baseUrl, username, oldPassword);

        byte[] newSalt = randomBytes(SALT_BYTES);
        byte[] newHash = pbkdf2(newPassword, newSalt, PBKDF2_ITERATIONS, DERIVED_KEY_LEN);

        Response resp = post(baseUrl, token, "/change-password", Json.object(
                "new_salt", bytesToHex(newSalt),
                "new_password_hash", bytesToHex(newHash),
                "new_iterations", PBKDF2_ITERATIONS));
        if (resp.status != 200 && resp.status != 204) {
            throw new SillyException(errorMessage(resp, "Change password failed"), resp.status, resp.body);
        }
    }

    /**
     * Invalidates the session identified by apiKey.
     *
     * @return the server's confirmation message, or null if the response had none
     */
    public static String logout(String baseUrl, String apiKey) throws SillyException {
        if (baseUrl == null || apiKey == null) {
            throw new SillyException("baseUrl and apiKey are required", 0, null);
        }
        Response resp = get(baseUrl, apiKey, "/logout");
        if (resp.status != 200) {
            throw new SillyException(errorMessage(resp, "Logout failed"), resp.status, resp.body);
        }
        try {
            return Json.parseObject(resp.body).get("msg");
        } catch (RuntimeException notJson) {
            return null;
        }
    }

    /* ------------------------------------------------------------------ */
    /* Crypto: PBKDF2-HMAC-SHA256, HMAC-SHA256, random bytes               */
    /* ------------------------------------------------------------------ */

    /**
     * SunJCE's "PBKDF2WithHmacSHA1" is documented (and well-known) to
     * truncate each password char to its low 8 bits rather than encoding
     * it as UTF-8, which would silently diverge from Python's
     * hashlib.pbkdf2_hmac/Node's crypto.pbkdf2/OpenSSL's PKCS5_PBKDF2_HMAC
     * for any non-ASCII password. Confirmed by hand that the newer
     * "PBKDF2WithHmacSHA256" used here does not share that behavior -- it
     * already UTF-8-encodes the char[] internally, matching the other
     * three bindings byte-for-byte with no workaround (verified against
     * Python's hashlib.pbkdf2_hmac with a password containing accented
     * Latin, currency, and CJK characters).
     */
    private static byte[] pbkdf2(char[] password, byte[] salt, int iterations, int keyLenBytes)
            throws SillyException {
        PBEKeySpec spec = new PBEKeySpec(password, salt, iterations, keyLenBytes * 8);
        try {
            SecretKeyFactory skf = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
            return skf.generateSecret(spec).getEncoded();
        } catch (GeneralSecurityException e) {
            throw new SillyException("PBKDF2 derivation failed: " + e.getMessage(), 0, null);
        } finally {
            spec.clearPassword();
        }
    }

    private static byte[] hmacSha256(byte[] key, byte[] message) throws SillyException {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(key, "HmacSHA256"));
            return mac.doFinal(message);
        } catch (GeneralSecurityException e) {
            throw new SillyException("HMAC computation failed: " + e.getMessage(), 0, null);
        }
    }

    private static byte[] randomBytes(int n) {
        byte[] b = new byte[n];
        new SecureRandom().nextBytes(b);
        return b;
    }

    /* ------------------------------------------------------------------ */
    /* hex / byte helpers                                                  */
    /* ------------------------------------------------------------------ */

    private static final char[] HEX_DIGITS = "0123456789abcdef".toCharArray();

    private static String bytesToHex(byte[] bytes) {
        char[] out = new char[bytes.length * 2];
        for (int i = 0; i < bytes.length; i++) {
            int v = bytes[i] & 0xFF;
            out[i * 2] = HEX_DIGITS[v >>> 4];
            out[i * 2 + 1] = HEX_DIGITS[v & 0xF];
        }
        return new String(out);
    }

    private static byte[] hexToBytes(String hex) throws SillyException {
        if (hex == null || hex.length() % 2 != 0) {
            throw new SillyException("Invalid hex string from server", 0, null);
        }
        byte[] out = new byte[hex.length() / 2];
        for (int i = 0; i < out.length; i++) {
            int hi = Character.digit(hex.charAt(i * 2), 16);
            int lo = Character.digit(hex.charAt(i * 2 + 1), 16);
            if (hi < 0 || lo < 0) {
                throw new SillyException("Invalid hex string from server", 0, null);
            }
            out[i] = (byte) ((hi << 4) | lo);
        }
        return out;
    }

    /* ------------------------------------------------------------------ */
    /* Minimal JSON encode/decode for this API's flat request/response     */
    /* shapes only -- no nested objects/arrays, since none of the          */
    /* endpoints used here ever produce or expect any.                     */
    /* ------------------------------------------------------------------ */

    private static final class Json {
        private Json() {}

        /** Builds a flat {"k":"v",...} object. Values are String (quoted+escaped) or Integer (bare). */
        static String object(Object... kv) {
            StringBuilder sb = new StringBuilder("{");
            for (int i = 0; i < kv.length; i += 2) {
                if (i > 0) {
                    sb.append(',');
                }
                sb.append('"').append(kv[i]).append("\":");
                Object value = kv[i + 1];
                if (value instanceof Integer || value instanceof Long) {
                    sb.append(value);
                } else {
                    sb.append('"').append(escape(String.valueOf(value))).append('"');
                }
            }
            return sb.append('}').toString();
        }

        private static String escape(String s) {
            StringBuilder sb = new StringBuilder(s.length());
            for (int i = 0; i < s.length(); i++) {
                char c = s.charAt(i);
                switch (c) {
                    case '"':
                        sb.append("\\\"");
                        break;
                    case '\\':
                        sb.append("\\\\");
                        break;
                    case '\n':
                        sb.append("\\n");
                        break;
                    case '\r':
                        sb.append("\\r");
                        break;
                    case '\t':
                        sb.append("\\t");
                        break;
                    default:
                        if (c < 0x20) {
                            sb.append(String.format("\\u%04x", (int) c));
                        } else {
                            sb.append(c);
                        }
                }
            }
            return sb.toString();
        }

        /**
         * Parses a single-level JSON object into a key -> raw-value map.
         * String values are unescaped; numbers/literals are kept as their
         * literal text (callers that need an int call Integer.parseInt on
         * the result).
         */
        static Map<String, String> parseObject(String json) {
            if (json == null) {
                throw new IllegalArgumentException("null body");
            }
            int[] pos = {skipWs(json, 0)};
            expect(json, pos, '{');
            Map<String, String> map = new LinkedHashMap<>();
            pos[0] = skipWs(json, pos[0]);
            if (peek(json, pos) == '}') {
                pos[0]++;
                return map;
            }
            while (true) {
                pos[0] = skipWs(json, pos[0]);
                String key = parseString(json, pos);
                pos[0] = skipWs(json, pos[0]);
                expect(json, pos, ':');
                pos[0] = skipWs(json, pos[0]);
                String value = (peek(json, pos) == '"') ? parseString(json, pos) : parseLiteral(json, pos);
                map.put(key, value);
                pos[0] = skipWs(json, pos[0]);
                char c = peek(json, pos);
                pos[0]++;
                if (c == ',') {
                    continue;
                }
                if (c == '}') {
                    break;
                }
                throw new IllegalArgumentException("malformed JSON object at " + pos[0]);
            }
            return map;
        }

        private static String parseString(String json, int[] pos) {
            expect(json, pos, '"');
            StringBuilder sb = new StringBuilder();
            while (true) {
                char c = peek(json, pos);
                pos[0]++;
                if (c == '"') {
                    return sb.toString();
                }
                if (c == '\\') {
                    char esc = peek(json, pos);
                    pos[0]++;
                    switch (esc) {
                        case '"':
                            sb.append('"');
                            break;
                        case '\\':
                            sb.append('\\');
                            break;
                        case '/':
                            sb.append('/');
                            break;
                        case 'b':
                            sb.append('\b');
                            break;
                        case 'f':
                            sb.append('\f');
                            break;
                        case 'n':
                            sb.append('\n');
                            break;
                        case 'r':
                            sb.append('\r');
                            break;
                        case 't':
                            sb.append('\t');
                            break;
                        case 'u':
                            sb.append((char) Integer.parseInt(json.substring(pos[0], pos[0] + 4), 16));
                            pos[0] += 4;
                            break;
                        default:
                            throw new IllegalArgumentException("bad escape at " + pos[0]);
                    }
                } else {
                    sb.append(c);
                }
            }
        }

        private static String parseLiteral(String json, int[] pos) {
            int start = pos[0];
            while (pos[0] < json.length() && ",}".indexOf(json.charAt(pos[0])) < 0
                    && !Character.isWhitespace(json.charAt(pos[0]))) {
                pos[0]++;
            }
            return json.substring(start, pos[0]);
        }

        private static int skipWs(String json, int i) {
            while (i < json.length() && Character.isWhitespace(json.charAt(i))) {
                i++;
            }
            return i;
        }

        private static char peek(String json, int[] pos) {
            if (pos[0] >= json.length()) {
                throw new IllegalArgumentException("unexpected end of JSON");
            }
            return json.charAt(pos[0]);
        }

        private static void expect(String json, int[] pos, char c) {
            if (peek(json, pos) != c) {
                throw new IllegalArgumentException("expected '" + c + "' at " + pos[0]);
            }
            pos[0]++;
        }
    }
}
