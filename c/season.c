#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <cjson/cJSON.h>

#include "sillysite.h"

int main(int argc, char *argv[])
{
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <baseurl> <apikey> <year>\n", argv[0]);
        return 1;
    }

    const char *baseurl = argv[1];
    const char *apikey  = argv[2];
    const char *year    = argv[3];

    char path[64];
    snprintf(path, sizeof(path), "/season/%s", year);

    silly_response_t *resp = silly_get(baseurl, apikey, path);
    if (!resp) {
        fprintf(stderr, "Request failed: %s\n", strerror(errno));
        return 1;
    }

    if (resp->status == 401 || resp->status == 403) {
        fprintf(stderr, "Access denied (check your API key)\n");
        silly_response_free(resp);
        return 1;
    }
    if (resp->status == 404) {
        fprintf(stderr, "No data found for season %s\n", year);
        silly_response_free(resp);
        return 1;
    }
    if (resp->status != 200) {
        fprintf(stderr, "Server error %d: %s\n", resp->status,
                resp->error ? resp->error : resp->body ? resp->body : "");
        silly_response_free(resp);
        return 1;
    }

    cJSON *races = cJSON_Parse(resp->body);
    silly_response_free(resp);
    if (!races) {
        fprintf(stderr, "Failed to parse response\n");
        return 1;
    }

    printf("Season %s results:\n\n", year);
    printf("  %-3s  %-42s  %-24s  %s\n", "Rd.", "Grand Prix", "Winner", "Team");
    printf("  %-3s  %-42s  %-24s  %s\n",
           "---", "------------------------------------------",
           "------------------------", "--------------------");

    cJSON *race;
    cJSON_ArrayForEach(race, races) {
        cJSON *j_seq    = cJSON_GetObjectItem(race, "sequence_number");
        cJSON *j_name   = cJSON_GetObjectItem(race, "name");
        cJSON *j_driver = cJSON_GetObjectItem(race, "winning_driver");
        cJSON *j_team   = cJSON_GetObjectItem(race, "winning_team");

        int         seq    = j_seq    && cJSON_IsNumber(j_seq)  ? j_seq->valueint : 0;
        const char *name   = j_name   && cJSON_IsString(j_name)   ? j_name->valuestring   : "?";
        const char *driver = j_driver && cJSON_IsString(j_driver) ? j_driver->valuestring : "N/A";
        const char *team   = j_team   && cJSON_IsString(j_team)   ? j_team->valuestring   : "N/A";

        printf("  %-3d  %-42s  %-24s  %s\n", seq, name, driver, team);
    }

    cJSON_Delete(races);
    return 0;
}
