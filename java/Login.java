import java.util.Arrays;

/**
 * Usage: java Login <baseurl> <username>
 *
 * Prompts for the password, performs the challenge/response login, and
 * prints the session token to stdout -- one line, no decoration. Mirrors
 * ../login.py, ../c/login.c, and ../js/login.js.
 */
public final class Login {
    private Login() {}

    public static void main(String[] args) {
        if (args.length != 2) {
            System.err.println("Usage: Login <baseurl> <username>");
            System.exit(1);
            return;
        }
        String baseUrl = args[0];
        String username = args[1];

        char[] password = Readpass.readPassword("Password: ");

        // System.exit() skips any pending finally block, so the exit code
        // is computed here and exit happens once, after cleanup below --
        // not inside the try, where it would leave the password unwiped.
        int exitCode = 0;
        try {
            String token = Sillysite.login(baseUrl, username, password);
            System.out.println(token);
        } catch (Sillysite.SillyException e) {
            System.err.println("Login failed: " + e.getMessage());
            exitCode = 1;
        } finally {
            Arrays.fill(password, '\0');
        }
        System.exit(exitCode);
    }
}
