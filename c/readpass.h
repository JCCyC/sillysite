#ifndef READPASS_H
#define READPASS_H

#include <stdio.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

/*
 * read_password — prompt for a password on /dev/tty with echo disabled.
 *
 * Writes at most buflen-1 characters into buf (NUL-terminated).
 * Returns the number of characters read, or -1 on error.
 */
static inline int read_password(const char *prompt, char *buf, size_t buflen)
{
    FILE *tty = fopen("/dev/tty", "r+");
    if (!tty) { perror("fopen /dev/tty"); return -1; }

    fprintf(tty, "%s", prompt);
    fflush(tty);

    struct termios old, noecho;
    int have_term = (tcgetattr(fileno(tty), &old) == 0);
    if (have_term) {
        noecho = old;
        noecho.c_lflag &= (tcflag_t)~(ECHO | ECHOE | ECHOK | ECHONL);
        tcsetattr(fileno(tty), TCSAFLUSH, &noecho);
    }

    int rc = -1;
    if (fgets(buf, (int)buflen, tty)) {
        size_t len = strlen(buf);
        if (len > 0 && buf[len-1] == '\n') buf[--len] = '\0';
        rc = (int)len;
    }

    if (have_term) {
        tcsetattr(fileno(tty), TCSAFLUSH, &old);
        fprintf(tty, "\n");
    }
    fclose(tty);
    return rc;
}

#endif /* READPASS_H */
