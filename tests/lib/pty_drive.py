#!/usr/bin/env python3
"""Run a command attached to a pty, feeding scripted answers to its prompts.

Needed because the C client (c/login, c/changepw) reads passwords from
/dev/tty directly rather than stdin, so a plain piped subprocess can't
drive it non-interactively -- it needs a real controlling terminal.

Usage:
    pty_drive.py <timeout_seconds> [<prompt> <answer>]... -- <command> [args...]

Waits for each <prompt> substring to appear in the child's output (in
order), then writes <answer> + newline. A short delay after the prompt is
seen gives the child time to disable terminal echo (it does so via
tcsetattr(..., TCSAFLUSH, ...) right after printing the prompt, which
discards any input already queued -- sending too early would be lost).
After all answers are sent, drains remaining output until the child exits
or the timeout elapses. Prints captured combined stdout+stderr, then exits
with the child's exit code.
"""
import os
import sys
import time
import select


def main():
    argv = sys.argv[1:]
    timeout = float(argv[0])
    sep = argv.index("--")
    pairs_flat = argv[1:sep]
    cmd = argv[sep + 1:]

    if len(pairs_flat) % 2 != 0:
        print("pty_drive: prompt/answer arguments must come in pairs", file=sys.stderr)
        sys.exit(2)
    pairs = list(zip(pairs_flat[0::2], pairs_flat[1::2]))

    pid, master_fd = os.forkpty()
    if pid == 0:
        try:
            os.execvp(cmd[0], cmd)
        except OSError:
            os._exit(127)

    deadline = time.time() + timeout
    buf = b""
    output = b""

    def read_more(timeout_s):
        nonlocal buf, output
        try:
            r, _, _ = select.select([master_fd], [], [], timeout_s)
        except (OSError, ValueError):
            return False
        if master_fd in r:
            try:
                chunk = os.read(master_fd, 4096)
            except OSError:
                return False
            if not chunk:
                return False
            buf += chunk
            output += chunk
            return True
        return None  # timed out, no data either way

    for prompt, answer in pairs:
        prompt_b = prompt.encode()
        found = False
        while time.time() < deadline:
            if prompt_b in buf:
                found = True
                break
            if read_more(0.2) is False:
                break
        if not found:
            break
        buf = buf.split(prompt_b, 1)[1]
        time.sleep(0.15)
        try:
            os.write(master_fd, (answer + "\n").encode())
        except OSError:
            break

    while time.time() < deadline:
        if read_more(0.3) is False:
            break

    try:
        os.close(master_fd)
    except OSError:
        pass

    status = 0
    try:
        wait_deadline = time.time() + 5
        while time.time() < wait_deadline:
            wpid, status = os.waitpid(pid, os.WNOHANG)
            if wpid != 0:
                break
            time.sleep(0.05)
    except ChildProcessError:
        status = 0

    sys.stdout.buffer.write(output)
    sys.stdout.flush()

    if os.WIFEXITED(status):
        sys.exit(os.WEXITSTATUS(status))
    elif os.WIFSIGNALED(status):
        sys.exit(128 + os.WTERMSIG(status))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
