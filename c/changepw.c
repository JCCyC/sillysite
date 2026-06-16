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

    char oldpw[1024], newpw[1024], confirmpw[1024];

    if (read_password("Current password: ",     oldpw,     sizeof(oldpw))     < 0 ||
        read_password("New password: ",         newpw,     sizeof(newpw))     < 0 ||
        read_password("Confirm new password: ", confirmpw, sizeof(confirmpw)) < 0) {
        fprintf(stderr, "Failed to read password\n");
        return 1;
    }

    if (strcmp(newpw, confirmpw) != 0) {
        memset(oldpw, 0, sizeof(oldpw));
        memset(newpw, 0, sizeof(newpw));
        memset(confirmpw, 0, sizeof(confirmpw));
        fprintf(stderr, "Change password failed: passwords do not match\n");
        return 1;
    }
    memset(confirmpw, 0, sizeof(confirmpw));

    int rc = silly_changepw(baseurl, username, oldpw, newpw);
    memset(oldpw, 0, sizeof(oldpw));
    memset(newpw, 0, sizeof(newpw));

    if (rc != 0) {
        fprintf(stderr, "Change password failed: %s\n", strerror(errno));
        return 1;
    }

    printf("Password changed successfully\n");
    return 0;
}
