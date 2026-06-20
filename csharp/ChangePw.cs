using System;

/// <summary>
/// Usage: mono ChangePw.exe &lt;baseurl&gt; &lt;username&gt;
///
/// Prompts for the current password, a new password, and a confirmation.
/// Verifies the two new-password entries match before proceeding. Mirrors
/// ../changepw.py, ../c/changepw.c, ../js/changepw.js, and ../java/ChangePw.java.
/// </summary>
public static class ChangePw
{
    public static int Main(string[] args)
    {
        if (args.Length != 2)
        {
            Console.Error.WriteLine("Usage: ChangePw <baseurl> <username>");
            return 1;
        }
        string baseUrl = args[0];
        string username = args[1];

        char[] oldPassword = Readpass.ReadPassword("Current password: ");
        char[] newPassword = Readpass.ReadPassword("New password: ");
        char[] confirmPassword = Readpass.ReadPassword("Confirm new password: ");

        int exitCode = 0;
        try
        {
            if (!PasswordsEqual(newPassword, confirmPassword))
            {
                Console.Error.WriteLine("Change password failed: passwords do not match");
                exitCode = 1;
            }
            else
            {
                Sillysite.ChangePw(baseUrl, username, oldPassword, newPassword);
                Console.WriteLine("Password changed successfully");
            }
        }
        catch (Sillysite.SillyException e)
        {
            Console.Error.WriteLine("Change password failed: " + e.Message);
            exitCode = 1;
        }
        finally
        {
            Array.Clear(oldPassword, 0, oldPassword.Length);
            Array.Clear(newPassword, 0, newPassword.Length);
            Array.Clear(confirmPassword, 0, confirmPassword.Length);
        }
        return exitCode;
    }

    private static bool PasswordsEqual(char[] a, char[] b)
    {
        if (a.Length != b.Length)
        {
            return false;
        }
        for (int i = 0; i < a.Length; i++)
        {
            if (a[i] != b[i])
            {
                return false;
            }
        }
        return true;
    }
}
