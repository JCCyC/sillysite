#ifndef SILLYSITE_H
#define SILLYSITE_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * silly_response_t - result of an HTTP call.
 *
 * Always free with silly_response_free().  Never free individual
 * members; the struct owns them.
 *
 *   status   HTTP status code (200, 404, …), or 0 on transport error
 *            (connect failed, DNS failure, timeout, …).
 *   body     NUL-terminated response body, or NULL if none/not yet set.
 *   error    Human-readable error string (transport or application),
 *            or NULL on success.
 *
 * errno is also set on every call — see individual function docs.
 */
typedef struct silly_response {
    int   status;
    char *body;
    char *error;
} silly_response_t;

void silly_response_free(silly_response_t *r);


/* ------------------------------------------------------------------ */
/* High-level auth helpers                                             */
/* ------------------------------------------------------------------ */

/*
 * silly_login — authenticate and obtain a session token.
 *
 * Returns a heap-allocated NUL-terminated token string that the
 * caller must free().  Returns NULL on any failure and sets errno:
 *
 *   EACCES   wrong credentials (server returned 403)
 *   ETIMEDOUT connect or response timed out
 *   ECONNREFUSED server not reachable
 *   EHOSTUNREACH hostname did not resolve
 *   EINVAL   malformed server response
 *   ENOMEM   allocation failure
 *   EIO      other / unexpected HTTP error
 */
char *silly_login(const char *baseurl, const char *username,
                  const char *password);

/*
 * silly_changepw — change a user's password.
 *
 * Logs in with oldpw to get a session token, derives a new PBKDF2
 * salt/hash/iterations from newpw locally (the new password is never
 * sent over the network), then posts the derived values to
 * /change-password.
 *
 * Returns 0 on success, -1 on failure (errno set as for silly_login,
 * plus EACCES if the server rejects the change).
 */
int silly_changepw(const char *baseurl, const char *username,
                   const char *oldpw, const char *newpw);

/*
 * silly_logout — invalidate a session token.
 *
 * Returns 0 on success, -1 on failure.
 * errno: EACCES (invalid/expired token), EINVAL (static API key has
 * no session), and the transport errors listed for silly_login.
 */
int silly_logout(const char *baseurl, const char *apikey);


/* ------------------------------------------------------------------ */
/* Raw HTTP helpers                                                     */
/* ------------------------------------------------------------------ */

/*
 * silly_get / silly_post / silly_put / silly_delete
 *
 * Perform an HTTP request against baseurl+path, optionally
 * authenticated with apikey (sent as X-API-Key header; pass NULL to
 * omit).  body is the JSON request body for POST/PUT (pass NULL for
 * an empty body).  silly_delete has no body parameter.
 *
 * Return a heap-allocated silly_response_t that the caller must free
 * with silly_response_free().  Return NULL (errno = ENOMEM) only if
 * the response struct itself could not be allocated — all other
 * outcomes, including transport errors, are reported through the
 * returned struct (status = 0, error set).
 *
 * errno is always set:
 *   0        success (2xx status)
 *   EACCES   401 or 403
 *   ENOENT   404
 *   EEXIST   409
 *   ETIMEDOUT timeout (transport or HTTP 408/504)
 *   ECONNREFUSED host refused connection
 *   EHOSTUNREACH DNS failure or unreachable host
 *   EIO      other HTTP or transport error
 *   ENOMEM   allocation failure (NULL returned)
 */
silly_response_t *silly_get(const char *baseurl, const char *apikey,
                             const char *path);
silly_response_t *silly_post(const char *baseurl, const char *apikey,
                              const char *path, const char *body);
silly_response_t *silly_put(const char *baseurl, const char *apikey,
                             const char *path, const char *body);
silly_response_t *silly_delete(const char *baseurl, const char *apikey,
                                const char *path);

#ifdef __cplusplus
}
#endif
#endif /* SILLYSITE_H */
