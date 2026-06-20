import java.util.Arrays;

/**
 * Usage: java ChangePw <baseurl> <username>
 *
 * Prompts for the current password, a new password, and a confirmation.
 * Verifies the two new-password entries match before proceeding. Mirrors
 * ../changepw.py, ../c/changepw.c, and ../js/changepw.js.
 */
public final class ChangePw {
    private ChangePw() {}

    public static void main(String[] args) {
        if (args.length != 2) {
            System.err.println("Usage: ChangePw <baseurl> <username>");
            System.exit(1);
            return;
        }
        String baseUrl = args[0];
        String username = args[1];

        char[] oldPassword = Readpass.readPassword("Current password: ");
        char[] newPassword = Readpass.readPassword("New password: ");
        char[] confirmPassword = Readpass.readPassword("Confirm new password: ");

        // System.exit() skips any pending finally block, so the exit code
        // is computed here and exit happens once, after cleanup below --
        // not inside the try, where it would leave passwords unwiped.
        int exitCode = 0;
        try {
            if (!Arrays.equals(newPassword, confirmPassword)) {
                System.err.println("Change password failed: passwords do not match");
                exitCode = 1;
            } else {
                Sillysite.changepw(baseUrl, username, oldPassword, newPassword);
                System.out.println("Password changed successfully");
            }
        } catch (Sillysite.SillyException e) {
            System.err.println("Change password failed: " + e.getMessage());
            exitCode = 1;
        } finally {
            Arrays.fill(oldPassword, '\0');
            Arrays.fill(newPassword, '\0');
            Arrays.fill(confirmPassword, '\0');
        }
        System.exit(exitCode);
    }
}
