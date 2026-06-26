#!/usr/bin/env php
<?php
/**
 * Usage: ./changepw.php <baseurl> <username>
 *
 * Prompts for the current password, a new password, and a confirmation.
 * Verifies the two new-password entries match before proceeding. Mirrors
 * ../changepw.py, ../c/changepw.c, ../js/changepw.js, ../java/ChangePw.java,
 * and ../csharp/ChangePw.cs.
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

    $oldPassword = readPassword("Current password: ");
    $newPassword = readPassword("New password: ");
    $confirmPassword = readPassword("Confirm new password: ");

    if ($newPassword !== $confirmPassword) {
        fwrite(STDERR, "Change password failed: passwords do not match\n");
        return 1;
    }

    try {
        Sillysite::changepw($baseUrl, $username, $oldPassword, $newPassword);
        echo "Password changed successfully\n";
        return 0;
    } catch (SillysiteException $e) {
        fwrite(STDERR, "Change password failed: " . $e->getMessage() . "\n");
        return 1;
    }
}

exit(main());
