#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sillysite.h"
#include "readpass.h"

int main(int argc, char *argv[])
{
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <baseurl> <username>\n", argv[0]);
        return 1;
    }

    const char *baseurl  = argv[1];
    const char *username = argv[2];

    char password[1024];
    if (read_password("Password: ", password, sizeof(password)) < 0) {
        fprintf(stderr, "Failed to read password\n");
        return 1;
    }

    char *token = silly_login(baseurl, username, password);
    memset(password, 0, sizeof(password));

    if (!token) {
        fprintf(stderr, "Login failed: %s\n", strerror(errno));
        return 1;
    }

    printf("%s\n", token);
    free(token);
    return 0;
}
