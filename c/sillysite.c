#include <errno.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <curl/curl.h>
#include <cjson/cJSON.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/rand.h>

#include "sillysite.h"

#define DERIVED_KEY_LEN   32
#define PBKDF2_ITERATIONS 200000
#define NEW_SALT_BYTES    16

/* ------------------------------------------------------------------ */
/* libcurl one-time global init                                        */
/* ------------------------------------------------------------------ */

static pthread_once_t g_curl_once = PTHREAD_ONCE_INIT;
static void do_curl_init(void) { curl_global_init(CURL_GLOBAL_DEFAULT); }

/* ------------------------------------------------------------------ */
/* Grow buffer used as curl write target                               */
/* ------------------------------------------------------------------ */

typedef struct { char *data; size_t len; } grow_buf_t;

static size_t on_write(char *ptr, size_t sz, size_t nmemb, void *ud)
{
    grow_buf_t *b = ud;
    size_t n = sz * nmemb;
    char *tmp = realloc(b->data, b->len + n + 1);
    if (!tmp) return 0;
    b->data = tmp;
    memcpy(b->data + b->len, ptr, n);
    b->len += n;
    b->data[b->len] = '\0';
    return n;
}

/* ------------------------------------------------------------------ */
/* Hex helpers                                                         */
/* ------------------------------------------------------------------ */

static void hex_enc(const unsigned char *in, size_t len, char *out)
{
    static const char h[] = "0123456789abcdef";
    for (size_t i = 0; i < len; i++) {
        out[2*i]   = h[in[i] >> 4];
        out[2*i+1] = h[in[i] & 0xf];
    }
    out[2*len] = '\0';
}

static int nibble(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

/* Returns number of decoded bytes, or -1 on malformed input. */
static int hex_dec(const char *in, unsigned char *out, size_t max_out)
{
    size_t slen = strlen(in);
    if (slen % 2) return -1;
    size_t n = slen / 2;
    if (n > max_out) return -1;
    for (size_t i = 0; i < n; i++) {
        int hi = nibble(in[2*i]), lo = nibble(in[2*i+1]);
        if (hi < 0 || lo < 0) return -1;
        out[i] = (unsigned char)(hi << 4 | lo);
    }
    return (int)n;
}

/* ------------------------------------------------------------------ */
/* URL builder                                                         */
/* ------------------------------------------------------------------ */

static char *build_url(const char *baseurl, const char *path)
{
    size_t blen = strlen(baseurl);
    while (blen > 0 && baseurl[blen-1] == '/') blen--;
    const char *sep = (path && path[0] == '/') ? "" : "/";
    size_t plen = path ? strlen(path) : 0;
    size_t total = blen + strlen(sep) + plen + 1;
    char *url = malloc(total);
    if (!url) return NULL;
    snprintf(url, total, "%.*s%s%s", (int)blen, baseurl, sep, path ? path : "");
    return url;
}

/* ------------------------------------------------------------------ */
/* errno mapping                                                       */
/* ------------------------------------------------------------------ */

static void errno_from_curl(CURLcode rc)
{
    switch (rc) {
    case CURLE_OPERATION_TIMEDOUT:   errno = ETIMEDOUT;    break;
    case CURLE_COULDNT_CONNECT:      errno = ECONNREFUSED; break;
    case CURLE_COULDNT_RESOLVE_HOST:
    case CURLE_COULDNT_RESOLVE_PROXY:errno = EHOSTUNREACH; break;
    case CURLE_OUT_OF_MEMORY:        errno = ENOMEM;       break;
    default:                         errno = EIO;          break;
    }
}

static void errno_from_status(int status)
{
    if (status >= 200 && status < 300) { errno = 0;           return; }
    switch (status) {
    case 401: case 403:              errno = EACCES;       break;
    case 404:                        errno = ENOENT;       break;
    case 408: case 504:              errno = ETIMEDOUT;    break;
    case 409:                        errno = EEXIST;       break;
    default:                         errno = EIO;          break;
    }
}

/* ------------------------------------------------------------------ */
/* Core HTTP dispatcher                                                */
/* ------------------------------------------------------------------ */

static silly_response_t *http_do(const char *method, const char *url,
                                  const char *apikey, const char *json_body)
{
    pthread_once(&g_curl_once, do_curl_init);

    silly_response_t *resp = calloc(1, sizeof(*resp));
    if (!resp) { errno = ENOMEM; return NULL; }

    grow_buf_t buf = {NULL, 0};

    CURL *curl = curl_easy_init();
    if (!curl) { free(resp); errno = ENOMEM; return NULL; }

    struct curl_slist *hdrs = NULL;
    hdrs = curl_slist_append(hdrs, "Content-Type: application/json");
    if (apikey) {
        char hdr[1024];
        if (snprintf(hdr, sizeof(hdr), "X-API-Key: %s", apikey) >= (int)sizeof(hdr)) {
            curl_slist_free_all(hdrs);
            curl_easy_cleanup(curl);
            free(resp);
            errno = EINVAL;
            return NULL;
        }
        hdrs = curl_slist_append(hdrs, hdr);
    }

    curl_easy_setopt(curl, CURLOPT_URL,            url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER,     hdrs);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION,  on_write);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA,      &buf);
    curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, 10L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT,        30L);
    curl_easy_setopt(curl, CURLOPT_NOSIGNAL,       1L);

    const char *body    = json_body ? json_body : "";
    long        bodylen = (long)(json_body ? strlen(json_body) : 0);

    if (strcmp(method, "GET") == 0) {
        /* default */
    } else if (strcmp(method, "POST") == 0) {
        curl_easy_setopt(curl, CURLOPT_POST,          1L);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS,    body);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, bodylen);
    } else if (strcmp(method, "PUT") == 0) {
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PUT");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS,    body);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, bodylen);
    } else if (strcmp(method, "DELETE") == 0) {
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");
    }

    CURLcode rc = curl_easy_perform(curl);

    if (rc != CURLE_OK) {
        resp->status = 0;
        resp->error  = strdup(curl_easy_strerror(rc));
        errno_from_curl(rc);
    } else {
        long status = 0;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &status);
        resp->status = (int)status;
        resp->body   = buf.data;
        buf.data     = NULL;
        errno_from_status(resp->status);
    }

    free(buf.data);
    curl_slist_free_all(hdrs);
    curl_easy_cleanup(curl);
    return resp;
}

/* ------------------------------------------------------------------ */
/* Public response free                                                */
/* ------------------------------------------------------------------ */

void silly_response_free(silly_response_t *r)
{
    if (!r) return;
    free(r->body);
    free(r->error);
    free(r);
}

/* ------------------------------------------------------------------ */
/* Public HTTP helpers                                                 */
/* ------------------------------------------------------------------ */

silly_response_t *silly_get(const char *baseurl, const char *apikey,
                             const char *path)
{
    char *url = build_url(baseurl, path);
    if (!url) { errno = ENOMEM; return NULL; }
    silly_response_t *r = http_do("GET", url, apikey, NULL);
    free(url);
    return r;
}

silly_response_t *silly_post(const char *baseurl, const char *apikey,
                              const char *path, const char *body)
{
    char *url = build_url(baseurl, path);
    if (!url) { errno = ENOMEM; return NULL; }
    silly_response_t *r = http_do("POST", url, apikey, body);
    free(url);
    return r;
}

silly_response_t *silly_put(const char *baseurl, const char *apikey,
                             const char *path, const char *body)
{
    char *url = build_url(baseurl, path);
    if (!url) { errno = ENOMEM; return NULL; }
    silly_response_t *r = http_do("PUT", url, apikey, body);
    free(url);
    return r;
}

silly_response_t *silly_delete(const char *baseurl, const char *apikey,
                                const char *path)
{
    char *url = build_url(baseurl, path);
    if (!url) { errno = ENOMEM; return NULL; }
    silly_response_t *r = http_do("DELETE", url, apikey, NULL);
    free(url);
    return r;
}

/* ------------------------------------------------------------------ */
/* Internal login helper — returns malloc'd token or NULL             */
/* ------------------------------------------------------------------ */

static char *do_login(const char *baseurl, const char *username,
                      const char *password)
{
    /* -- Step 1: request a challenge -- */
    cJSON *jreq = cJSON_CreateObject();
    if (!jreq) { errno = ENOMEM; return NULL; }
    cJSON_AddStringToObject(jreq, "username", username);
    char *req_body = cJSON_PrintUnformatted(jreq);
    cJSON_Delete(jreq);
    if (!req_body) { errno = ENOMEM; return NULL; }

    silly_response_t *resp = silly_post(baseurl, NULL, "/login/challenge", req_body);
    free(req_body);
    if (!resp) return NULL;

    if (resp->status != 200) {
        errno_from_status(resp->status);
        silly_response_free(resp);
        return NULL;
    }

    /* -- Parse challenge response, copy strings before freeing JSON -- */
    cJSON *root = cJSON_Parse(resp->body);
    silly_response_free(resp);
    if (!root) { errno = EINVAL; return NULL; }

    cJSON *j_chall = cJSON_GetObjectItem(root, "challenge");
    cJSON *j_salt  = cJSON_GetObjectItem(root, "salt");
    cJSON *j_iter  = cJSON_GetObjectItem(root, "iterations");

    if (!cJSON_IsString(j_chall) || !cJSON_IsString(j_salt) || !cJSON_IsNumber(j_iter)) {
        cJSON_Delete(root);
        errno = EINVAL;
        return NULL;
    }

    char challenge_hex[512], salt_hex[512];
    strncpy(challenge_hex, j_chall->valuestring, sizeof(challenge_hex) - 1);
    challenge_hex[sizeof(challenge_hex)-1] = '\0';
    strncpy(salt_hex, j_salt->valuestring, sizeof(salt_hex) - 1);
    salt_hex[sizeof(salt_hex)-1] = '\0';
    int iterations = j_iter->valueint;
    cJSON_Delete(root);

    /* -- Decode salt, run PBKDF2 -- */
    unsigned char salt_bytes[256];
    int salt_len = hex_dec(salt_hex, salt_bytes, sizeof(salt_bytes));
    if (salt_len < 0) { errno = EINVAL; return NULL; }

    unsigned char derived_key[DERIVED_KEY_LEN];
    if (!PKCS5_PBKDF2_HMAC(password, (int)strlen(password),
                            salt_bytes, salt_len, iterations,
                            EVP_sha256(), DERIVED_KEY_LEN, derived_key)) {
        errno = EIO;
        return NULL;
    }

    /* -- Decode challenge, compute HMAC-SHA256 -- */
    unsigned char challenge_bytes[256];
    int challenge_len = hex_dec(challenge_hex, challenge_bytes, sizeof(challenge_bytes));
    if (challenge_len < 0) { errno = EINVAL; return NULL; }

    unsigned char hmac_out[EVP_MAX_MD_SIZE];
    unsigned int  hmac_len = 0;
    if (!HMAC(EVP_sha256(), derived_key, DERIVED_KEY_LEN,
              challenge_bytes, (size_t)challenge_len, hmac_out, &hmac_len)) {
        errno = EIO;
        return NULL;
    }

    char response_hex[2 * EVP_MAX_MD_SIZE + 1];
    hex_enc(hmac_out, hmac_len, response_hex);

    /* -- Step 2: submit response -- */
    jreq = cJSON_CreateObject();
    if (!jreq) { errno = ENOMEM; return NULL; }
    cJSON_AddStringToObject(jreq, "username",  username);
    cJSON_AddStringToObject(jreq, "challenge", challenge_hex);
    cJSON_AddStringToObject(jreq, "response",  response_hex);
    req_body = cJSON_PrintUnformatted(jreq);
    cJSON_Delete(jreq);
    if (!req_body) { errno = ENOMEM; return NULL; }

    resp = silly_post(baseurl, NULL, "/login/response", req_body);
    free(req_body);
    if (!resp) return NULL;

    if (resp->status != 200) {
        errno = (resp->status == 403) ? EACCES : EIO;
        silly_response_free(resp);
        return NULL;
    }

    /* -- Extract token -- */
    root = cJSON_Parse(resp->body);
    silly_response_free(resp);
    if (!root) { errno = EINVAL; return NULL; }

    cJSON *j_token = cJSON_GetObjectItem(root, "token");
    if (!cJSON_IsString(j_token)) { cJSON_Delete(root); errno = EINVAL; return NULL; }

    char *token = strdup(j_token->valuestring);
    cJSON_Delete(root);
    if (!token) { errno = ENOMEM; return NULL; }

    return token;
}

/* ------------------------------------------------------------------ */
/* Public auth helpers                                                 */
/* ------------------------------------------------------------------ */

char *silly_login(const char *baseurl, const char *username,
                  const char *password)
{
    if (!baseurl || !username || !password) { errno = EINVAL; return NULL; }
    return do_login(baseurl, username, password);
}

int silly_changepw(const char *baseurl, const char *username,
                   const char *oldpw, const char *newpw)
{
    if (!baseurl || !username || !oldpw || !newpw) { errno = EINVAL; return -1; }

    char *token = do_login(baseurl, username, oldpw);
    if (!token) return -1;

    /* Derive new credentials locally — new password never leaves the machine */
    unsigned char new_salt[NEW_SALT_BYTES];
    if (RAND_bytes(new_salt, NEW_SALT_BYTES) != 1) {
        free(token);
        errno = EIO;
        return -1;
    }

    unsigned char new_hash[DERIVED_KEY_LEN];
    if (!PKCS5_PBKDF2_HMAC(newpw, (int)strlen(newpw),
                            new_salt, NEW_SALT_BYTES, PBKDF2_ITERATIONS,
                            EVP_sha256(), DERIVED_KEY_LEN, new_hash)) {
        free(token);
        errno = EIO;
        return -1;
    }

    char new_salt_hex[2 * NEW_SALT_BYTES + 1];
    char new_hash_hex[2 * DERIVED_KEY_LEN + 1];
    hex_enc(new_salt, NEW_SALT_BYTES, new_salt_hex);
    hex_enc(new_hash, DERIVED_KEY_LEN, new_hash_hex);

    cJSON *jreq = cJSON_CreateObject();
    if (!jreq) { free(token); errno = ENOMEM; return -1; }
    cJSON_AddStringToObject(jreq, "new_salt",          new_salt_hex);
    cJSON_AddStringToObject(jreq, "new_password_hash", new_hash_hex);
    cJSON_AddNumberToObject(jreq, "new_iterations",    PBKDF2_ITERATIONS);
    char *req_body = cJSON_PrintUnformatted(jreq);
    cJSON_Delete(jreq);
    if (!req_body) { free(token); errno = ENOMEM; return -1; }

    silly_response_t *resp = silly_post(baseurl, token, "/change-password", req_body);
    free(req_body);
    free(token);

    if (!resp) return -1;
    int ok = (resp->status == 204 || resp->status == 200);
    if (!ok) errno_from_status(resp->status);
    silly_response_free(resp);
    return ok ? 0 : -1;
}

int silly_logout(const char *baseurl, const char *apikey)
{
    if (!baseurl || !apikey) { errno = EINVAL; return -1; }

    silly_response_t *resp = silly_get(baseurl, apikey, "/logout");
    if (!resp) return -1;

    int ok = (resp->status == 200);
    if (!ok) errno_from_status(resp->status);
    silly_response_free(resp);
    return ok ? 0 : -1;
}
