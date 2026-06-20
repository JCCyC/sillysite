using System;
using System.IO;
using System.Text;

/// <summary>
/// Prompts for a password on stdin, masking input (with '*' characters --
/// unlike Java's Console.readPassword()/c's termios no-echo, the BCL has no
/// built-in no-echo console read, so per-keystroke masking via
/// Console.ReadKey is the standard fallback) when stdin is a real terminal,
/// and falling back to a plain line read otherwise -- same behavior as
/// java/Readpass.java and js/readpass.js (which mask under a real terminal
/// and read plain lines when piped) rather than the C client's design
/// (which requires a real terminal/pty).
/// </summary>
internal static class Readpass
{
    // Lazily created once and reused across every ReadPassword() call in
    // this process. A fresh reader per call would each try to refill its
    // own internal buffer from stdin -- if piped input arrives as one
    // burst, the first reader can buffer lines meant for later prompts,
    // and that buffered data is lost once the reader is discarded (see
    // java/Readpass.java's and js/readpass.js's comments on the same
    // hazard).
    private static TextReader fallbackReader;

    public static char[] ReadPassword(string prompt)
    {
        Console.Write(prompt);
        if (!Console.IsInputRedirected)
        {
            return ReadMasked();
        }

        Console.Out.Flush();
        if (fallbackReader == null)
        {
            fallbackReader = new StreamReader(Console.OpenStandardInput(), new UTF8Encoding(false));
        }
        string line = fallbackReader.ReadLine();
        // A real terminal echoes the Enter keypress as a newline even with
        // input masked; piped stdin has no such echo, so without this the
        // prompt and whatever's printed next (e.g. the token) land on the
        // same line.
        Console.Out.WriteLine();
        if (line == null)
        {
            Console.Error.WriteLine("Unexpected end of input");
            Environment.Exit(1);
        }
        return line.ToCharArray();
    }

    private static char[] ReadMasked()
    {
        var buffer = new StringBuilder();
        while (true)
        {
            ConsoleKeyInfo key = Console.ReadKey(true);
            if (key.Key == ConsoleKey.Enter)
            {
                Console.Out.WriteLine();
                break;
            }
            if (key.Key == ConsoleKey.Backspace)
            {
                if (buffer.Length > 0)
                {
                    buffer.Length--;
                    Console.Write("\b \b");
                }
                continue;
            }
            if (key.KeyChar != '\0' && !char.IsControl(key.KeyChar))
            {
                buffer.Append(key.KeyChar);
                Console.Write('*');
            }
        }
        char[] result = new char[buffer.Length];
        buffer.CopyTo(0, result, 0, buffer.Length);
        return result;
    }
}
