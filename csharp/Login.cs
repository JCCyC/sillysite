using System;

/// <summary>
/// Usage: mono Login.exe &lt;baseurl&gt; &lt;username&gt;
///
/// Prompts for the password, performs the challenge/response login, and
/// prints the session token to stdout -- one line, no decoration. Mirrors
/// ../login.py, ../c/login.c, ../js/login.js, and ../java/Login.java.
/// </summary>
public static class Login
{
    public static int Main(string[] args)
    {
        if (args.Length != 2)
        {
            Console.Error.WriteLine("Usage: Login <baseurl> <username>");
            return 1;
        }
        string baseUrl = args[0];
        string username = args[1];

        char[] password = Readpass.ReadPassword("Password: ");

        // Environment.Exit() would skip any pending finally block, so the
        // exit code is computed and returned normally instead -- after
        // cleanup below, not before it, which would leave the password
        // unwiped.
        int exitCode = 0;
        try
        {
            string token = Sillysite.Login(baseUrl, username, password);
            Console.WriteLine(token);
        }
        catch (Sillysite.SillyException e)
        {
            Console.Error.WriteLine("Login failed: " + e.Message);
            exitCode = 1;
        }
        finally
        {
            Array.Clear(password, 0, password.Length);
        }
        return exitCode;
    }
}
