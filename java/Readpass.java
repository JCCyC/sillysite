import java.io.BufferedReader;
import java.io.Console;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

/**
 * Prompts for a password on stdin, masking input when stdin is a real
 * terminal (via {@link System#console()}), and falling back to a plain
 * line read otherwise -- same behavior as {@code js/readpass.js} (which
 * masks under a real terminal and reads plain lines when piped) rather
 * than the C client's design (which requires a real terminal/pty).
 */
final class Readpass {
    private Readpass() {}

    // Lazily created once and reused across every readPassword() call in
    // this process. A fresh BufferedReader per call would each try to
    // refill its own internal buffer from stdin -- if piped input arrives
    // as one burst, the first reader can buffer lines meant for later
    // prompts, and that buffered data is lost once the reader is discarded
    // (see js/readpass.js's comment on the same hazard).
    private static BufferedReader fallbackReader;

    static char[] readPassword(String prompt) {
        Console console = System.console();
        if (console != null) {
            char[] password = console.readPassword(prompt);
            if (password == null) {
                System.err.println("Unexpected end of input");
                System.exit(1);
            }
            return password;
        }

        System.out.print(prompt);
        System.out.flush();
        if (fallbackReader == null) {
            fallbackReader = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        }
        try {
            String line = fallbackReader.readLine();
            // A real terminal echoes the Enter keypress as a newline even
            // with input masked; piped stdin has no such echo, so without
            // this the prompt and whatever's printed next (e.g. the token)
            // land on the same line.
            System.out.println();
            if (line == null) {
                System.err.println("Unexpected end of input");
                System.exit(1);
            }
            return line.toCharArray();
        } catch (IOException e) {
            System.err.println("Failed to read password: " + e.getMessage());
            System.exit(1);
            throw new AssertionError("unreachable");
        }
    }
}
