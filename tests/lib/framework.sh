# Test registry and runner. Sourced by run_tests.sh after lib/api.sh and
# lib/docker.sh, and after all tests/cases/*.sh have registered their tests.

TEST_FN=()
TEST_SHORT=()
TEST_LONG=()

# register_test <function_name> <short description, <50 chars> <long description>
register_test() {
    local fn="$1" short="$2" long="$3"
    if [ "${#short}" -ge 50 ]; then
        echo "register_test: short description >=50 chars: $short" >&2
        exit 2
    fi
    TEST_FN+=("$fn")
    TEST_SHORT+=("$short")
    TEST_LONG+=("$long")
}

PASS_COUNT=0
FAIL_COUNT=0
FAILURE_SUMMARY=()

run_all_tests() {
    local total="${#TEST_FN[@]}"
    {
        echo "Silly Site test suite report"
        echo "Run started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "Total tests: $total"
        echo
    } > "$REPORT_FILE"

    local i fn short long n output rc
    for i in "${!TEST_FN[@]}"; do
        n=$((i + 1))
        fn="${TEST_FN[$i]}"
        short="${TEST_SHORT[$i]}"
        long="${TEST_LONG[$i]}"

        printf '#%d (%s)... ' "$n" "$short"

        output="$("$fn" 2>&1)"
        rc=$?

        if [ "$rc" -eq 0 ]; then
            printf 'PASS\n'
            PASS_COUNT=$((PASS_COUNT + 1))
            printf '#%d (%s)... PASS\n' "$n" "$short" >> "$REPORT_FILE"
        else
            printf 'FAIL\n'
            FAIL_COUNT=$((FAIL_COUNT + 1))
            FAILURE_SUMMARY+=("#$n $short")
            {
                printf '#%d (%s)... FAIL\n' "$n" "$short"
                printf '    %s\n' "$long"
                if [ -n "$output" ]; then
                    printf '    output:\n'
                    printf '      %s\n' "${output//$'\n'/$'\n'      }"
                fi
            } >> "$REPORT_FILE"
        fi
    done

    {
        echo
        echo "Run finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "Passed: $PASS_COUNT / $total"
        echo "Failed: $FAIL_COUNT / $total"
        if [ "$FAIL_COUNT" -gt 0 ]; then
            echo
            echo "Failed tests:"
            printf '  %s\n' "${FAILURE_SUMMARY[@]}"
        fi
    } >> "$REPORT_FILE"
}

# assert_eq <expected> <actual> [message]
assert_eq() {
    local expected="$1" actual="$2" msg="${3:-}"
    if [ "$expected" != "$actual" ]; then
        echo "expected [$expected] got [$actual]${msg:+ ($msg)}"
        return 1
    fi
}

# assert_contains <haystack> <needle> [message]
assert_contains() {
    local haystack="$1" needle="$2" msg="${3:-}"
    case "$haystack" in
        *"$needle"*) return 0 ;;
        *)
            echo "expected to find [$needle] in [$haystack]${msg:+ ($msg)}"
            return 1
            ;;
    esac
}

# assert_not_contains <haystack> <needle> [message]
assert_not_contains() {
    local haystack="$1" needle="$2" msg="${3:-}"
    case "$haystack" in
        *"$needle"*)
            echo "expected NOT to find [$needle] in [$haystack]${msg:+ ($msg)}"
            return 1
            ;;
        *) return 0 ;;
    esac
}
