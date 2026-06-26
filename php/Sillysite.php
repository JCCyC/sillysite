<?php
/**
 * SillySite API client library.
 *
 * Uses only core PHP -- stream contexts for HTTP (no curl extension
 * needed), and the bundled hash/json extensions (both enabled by default
 * in a plain `php-cli` install, no separate package) for PBKDF2/HMAC and
 * request/response bodies. No external dependencies, no Composer, no
 * namespace -- mirroring the zero-dependency design of js/sillysite.js,
 * java/Sillysite.java, and csharp/Sillysite.cs.
 *
 * Unlike those three, passwords here are plain `string`, not a
 * char[]/byte[] the caller can wipe after use: PHP strings are immutable
 * values with no reliable in-userland way to zero the underlying memory
 * (no mutable char array, no guaranteed-immediate garbage collection), so
 * there's no real wiping to do -- accepting a char[]-like type here would
 * be security theater rather than an actual improvement.
 */

final class SillysiteResponse
{
    /** @var int HTTP status code, or 0 on a transport-level failure (DNS, connection refused, timeout, ...). */
    public readonly int $status;
    /** @var ?string Response body, or null if none was received. */
    public readonly ?string $body;
    /** @var ?string Human-readable transport error, or null if an HTTP response was received. */
    public readonly ?string $error;

    public function __construct(int $status, ?string $body, ?string $error)
    {
        $this->status = $status;
        $this->body = $body;
        $this->error = $error;
    }
}

/** Thrown by the high-level auth methods (Sillysite::login/changepw/logout) on failure. */
final class SillysiteException extends \Exception
{
    /** @var int HTTP status code, or 0 if the failure was a transport error or an argument check. */
    public readonly int $status;
    /** @var ?string Response body, if any. */
    public readonly ?string $body;

    public function __construct(string $message, int $status, ?string $body)
    {
        parent::__construct($message);
        $this->status = $status;
        $this->body = $body;
    }
}

final class Sillysite
{
    private const PBKDF2_ITERATIONS = 200_000;
    private const DERIVED_KEY_LEN = 32;
    private const SALT_BYTES = 16;

    private function __construct()
    {
    }

    /* ------------------------------------------------------------------ */
    /* Raw HTTP helpers                                                    */
    /* ------------------------------------------------------------------ */

    /**
     * GET baseUrl+path, optionally authenticated with apiKey (sent as
     * X-API-Key; pass null to omit). Never throws: transport failures are
     * reported through the returned SillysiteResponse (status 0, error
     * set), the same as an ordinary HTTP error response.
     */
    public static function get(string $baseUrl, ?string $apiKey, string $path): SillysiteResponse
    {
        return self::request($baseUrl, $apiKey, "GET", $path, null);
    }

    /** POST baseUrl+path with a JSON request body (pass null for an empty body). */
    public static function post(string $baseUrl, ?string $apiKey, string $path, ?string $jsonBody): SillysiteResponse
    {
        return self::request($baseUrl, $apiKey, "POST", $path, $jsonBody);
    }

    /** PUT baseUrl+path with a JSON request body (pass null for an empty body). */
    public static function put(string $baseUrl, ?string $apiKey, string $path, ?string $jsonBody): SillysiteResponse
    {
        return self::request($baseUrl, $apiKey, "PUT", $path, $jsonBody);
    }

    /** DELETE baseUrl+path. */
    public static function delete(string $baseUrl, ?string $apiKey, string $path): SillysiteResponse
    {
        return self::request($baseUrl, $apiKey, "DELETE", $path, null);
    }

    private static function request(
        string $baseUrl,
        ?string $apiKey,
        string $method,
        string $path,
        ?string $jsonBody
    ): SillysiteResponse {
        $url = self::buildUrl($baseUrl, $path);

        $headers = "Content-Type: application/json\r\n";
        if ($apiKey !== null) {
            $headers .= "X-API-Key: " . $apiKey . "\r\n";
        }

        $options = [
            "method" => $method,
            "header" => $headers,
            "ignore_errors" => true,
            "timeout" => 30,
        ];
        // Always attach a body (even empty) for POST/PUT, matching the
        // other bindings, which all still send a Content-Type header on a
        // bodyless POST/PUT.
        if ($jsonBody !== null || $method === "POST" || $method === "PUT") {
            $options["content"] = $jsonBody ?? "";
        }

        $context = stream_context_create(["http" => $options]);
        $body = @file_get_contents($url, false, $context);

        if ($body === false) {
            $err = error_get_last();
            return new SillysiteResponse(0, null, $err["message"] ?? "request failed");
        }

        $status = 0;
        if (isset($http_response_header[0])
            && preg_match('{^HTTP/\S+\s+(\d+)}', $http_response_header[0], $m)) {
            $status = (int) $m[1];
        }
        return new SillysiteResponse($status, $body, null);
    }

    private static function buildUrl(string $baseUrl, string $path): string
    {
        $trimmed = rtrim($baseUrl, "/");
        $sep = ($path !== "" && $path[0] === "/") ? "" : "/";
        return $trimmed . $sep . $path;
    }

    private static function errorMessage(SillysiteResponse $resp, string $fallback): string
    {
        if ($resp->body !== null) {
            $data = json_decode($resp->body, true);
            if (is_array($data) && isset($data["detail"]) && is_string($data["detail"])) {
                return $data["detail"];
            }
        }
        return $resp->error ?? $fallback;
    }

    /** Decodes a JSON object response body, throwing SillysiteException on malformed JSON. */
    private static function decodeObject(SillysiteResponse $resp): array
    {
        $data = json_decode($resp->body ?? "", true);
        if (!is_array($data)) {
            throw new SillysiteException("Malformed JSON response from server", $resp->status, $resp->body);
        }
        return $data;
    }

    /* ------------------------------------------------------------------ */
    /* High-level auth flows                                               */
    /* ------------------------------------------------------------------ */

    /**
     * Performs the challenge/response login flow.
     *
     * @return string the session token
     * @throws SillysiteException
     */
    public static function login(string $baseUrl, string $username, string $password): string
    {
        return self::doLogin($baseUrl, $username, $password);
    }

    private static function doLogin(string $baseUrl, string $username, string $password): string
    {
        $challResp = self::post($baseUrl, null, "/login/challenge", json_encode(["username" => $username]));
        if ($challResp->status !== 200) {
            throw new SillysiteException(
                self::errorMessage($challResp, "Failed to obtain login challenge"),
                $challResp->status,
                $challResp->body
            );
        }
        $challengeData = self::decodeObject($challResp);
        $saltBytes = hex2bin($challengeData["salt"]);
        $challengeBytes = hex2bin($challengeData["challenge"]);
        $iterations = (int) $challengeData["iterations"];

        $derivedKey = hash_pbkdf2("sha256", $password, $saltBytes, $iterations, self::DERIVED_KEY_LEN, true);
        $hmacOut = hash_hmac("sha256", $challengeBytes, $derivedKey, true);

        $loginResp = self::post($baseUrl, null, "/login/response", json_encode([
            "username" => $username,
            "challenge" => $challengeData["challenge"],
            "response" => bin2hex($hmacOut),
        ]));
        if ($loginResp->status !== 200) {
            throw new SillysiteException(
                self::errorMessage($loginResp, "Invalid username or password"),
                $loginResp->status,
                $loginResp->body
            );
        }
        return self::decodeObject($loginResp)["token"];
    }

    /**
     * Logs in with oldPassword, then derives fresh credentials from
     * newPassword locally and submits them -- newPassword is never sent
     * over the network.
     *
     * @throws SillysiteException
     */
    public static function changepw(string $baseUrl, string $username, string $oldPassword, string $newPassword): void
    {
        $token = self::doLogin($baseUrl, $username, $oldPassword);

        $newSalt = random_bytes(self::SALT_BYTES);
        $newHash = hash_pbkdf2("sha256", $newPassword, $newSalt, self::PBKDF2_ITERATIONS, self::DERIVED_KEY_LEN, true);

        $resp = self::post($baseUrl, $token, "/change-password", json_encode([
            "new_salt" => bin2hex($newSalt),
            "new_password_hash" => bin2hex($newHash),
            "new_iterations" => self::PBKDF2_ITERATIONS,
        ]));
        if ($resp->status !== 200 && $resp->status !== 204) {
            throw new SillysiteException(self::errorMessage($resp, "Change password failed"), $resp->status, $resp->body);
        }
    }

    /**
     * Invalidates the session identified by apiKey.
     *
     * @return ?string the server's confirmation message, or null if the response had none
     * @throws SillysiteException
     */
    public static function logout(string $baseUrl, string $apiKey): ?string
    {
        $resp = self::get($baseUrl, $apiKey, "/logout");
        if ($resp->status !== 200) {
            throw new SillysiteException(self::errorMessage($resp, "Logout failed"), $resp->status, $resp->body);
        }
        $data = json_decode($resp->body ?? "", true);
        return is_array($data) && isset($data["msg"]) ? $data["msg"] : null;
    }
}
