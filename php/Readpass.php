<?php
/**
 * Prompts for a password on stdin, masking input (via `stty -echo` --
 * there's no built-in no-echo console read in PHP like Java's
 * Console.readPassword() or C's direct termios handling, so shelling out
 * to `stty` is the standard way to do this) when stdin is a real
 * terminal, and falling back to a plain line read otherwise -- same
 * behavior as java/Readpass.java and js/readpass.js (which mask under a
 * real terminal and read plain lines when piped) rather than the C
 * client's design (which requires a real terminal/pty).
 */
function readPassword(string $prompt): string
{
    // Checked once and cached, not on every call: calling posix_isatty()
    // on STDIN interleaved with fgets() reads -- as a fresh call on every
    // prompt would -- makes PHP's stream layer drop already-buffered
    // lookahead data ("N bytes of buffered data lost during stream
    // conversion" warning), corrupting later prompts when piped input
    // arrives as one burst (see the equivalent hazard noted in
    // js/readpass.js and java/Readpass.java, though the PHP mechanism is
    // different -- this one is specific to posix_isatty() itself, not to
    // creating multiple readers).
    static $isTty = null;
    if ($isTty === null) {
        $isTty = function_exists("posix_isatty") && posix_isatty(STDIN);
    }

    echo $prompt;

    if ($isTty) {
        system("stty -echo");
    }
    $line = fgets(STDIN);
    if ($isTty) {
        system("stty echo");
    }
    // stty -echo suppresses the terminal's echo of the Enter keypress too,
    // not just the typed characters -- and piped stdin has no echo at all
    // -- so without this, the prompt and whatever's printed next (e.g. the
    // token) land on the same line either way.
    echo "\n";

    if ($line === false) {
        fwrite(STDERR, "Unexpected end of input\n");
        exit(1);
    }
    return rtrim($line, "\r\n");
}
