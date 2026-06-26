#!/usr/bin/env php
<?php
/**
 * Usage: ./login.php <baseurl> <username>
 *
 * Prompts for the password, performs the challenge/response login, and
 * prints the session token to stdout -- one line, no decoration. Mirrors
 * ../login.py, ../c/login.c, ../js/login.js, ../java/Login.java, and
 * ../csharp/Login.cs.
 */
require __DIR__ . "/Sillysite.php";
require __DIR__ . "/Readpass.php";

function main(): int
{
    global $argv;
    if (count($argv) !== 3) {
        fwrite(STDERR, "Usage: " . basename($argv[0]) . " <baseurl> <username>\n");
        return 1;
    }
    [, $baseUrl, $username] = $argv;

    $password = readPassword("Password: ");

    try {
        $token = Sillysite::login($baseUrl, $username, $password);
        echo $token . "\n";
        return 0;
    } catch (SillysiteException $e) {
        fwrite(STDERR, "Login failed: " . $e->getMessage() . "\n");
        return 1;
    }
}

exit(main());
