"""Run the real script in a pseudo-terminal against the real caffeinate.

These only run on macOS. Each test briefly keeps the Mac awake and cleans up
after itself.
"""

import fcntl
import os
import pty
import select
import shutil
import signal
import struct
import subprocess
import sys
import termios
import time
import unittest

from support import SCRIPT

ROWS, COLS = 24, 80
HAS_CAFFEINATE = sys.platform == "darwin" and shutil.which("caffeinate") is not None


class ScriptInPty:
    """The script running in its own pseudo-terminal, with its screen output
    collected as raw bytes."""

    def __init__(self, *args):
        self.output = b""
        self.exit_code = None
        self.pid, self.fd = pty.fork()
        if self.pid == 0:  # child
            fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
            env = dict(os.environ, TERM="xterm-256color", LC_ALL="en_US.UTF-8", ESCDELAY="25")
            os.execve(sys.executable, [sys.executable, str(SCRIPT), *args], env)

    def read_for(self, seconds):
        """Collect output for a while (or until the terminal closes)."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            ready, _, _ = select.select([self.fd], [], [], 0.05)
            if ready:
                try:
                    chunk = os.read(self.fd, 65536)
                except OSError:
                    return
                if not chunk:
                    return
                self.output += chunk

    def read_until(self, text, timeout=5):
        deadline = time.monotonic() + timeout
        while text not in self.output and time.monotonic() < deadline:
            self.read_for(0.1)
        return text in self.output

    def send(self, keys):
        os.write(self.fd, keys)

    def wait(self, timeout=5):
        """Wait for the script to exit; returns its exit code, or None."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                self.exit_code = os.waitstatus_to_exitcode(status)
                self.read_for(0.2)
                return self.exit_code
            self.read_for(0.1)
        return None

    def close(self):
        if self.exit_code is None:
            try:
                os.kill(self.pid, signal.SIGKILL)
                os.waitpid(self.pid, 0)
            except (ProcessLookupError, ChildProcessError):
                pass
        os.close(self.fd)


def caffeinate_pids_for(pid):
    """PIDs of caffeinate processes tied to `pid` with -w."""
    result = subprocess.run(
        ["pgrep", "-f", f"^caffeinate .*-w {pid}$"], capture_output=True, text=True
    )
    return [int(p) for p in result.stdout.split()]


def wait_for_no_caffeinate(pid, timeout=5):
    deadline = time.monotonic() + timeout
    while caffeinate_pids_for(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    return not caffeinate_pids_for(pid)


@unittest.skipUnless(HAS_CAFFEINATE, "needs macOS with caffeinate")
class EndToEndTest(unittest.TestCase):
    def start(self, *args):
        script = ScriptInPty(*args)
        self.addCleanup(self.ensure_no_caffeinate, script.pid)
        self.addCleanup(script.close)
        self.assertTrue(script.read_until(b"ACTIVE"), "status bar never showed ACTIVE")
        return script

    def ensure_no_caffeinate(self, pid):
        # Never leave a test's caffeinate running, even when the test failed.
        for child in caffeinate_pids_for(pid):
            os.kill(child, signal.SIGTERM)

    def test_rain_and_active_status_while_running(self):
        script = self.start()
        script.read_for(1)
        self.assertTrue(any(c.encode() in script.output for c in "ｱｲｳｴｵｶｷｸｹｺ"))
        self.assertIn(b"caffeinate -ds", script.output)
        self.assertEqual(len(caffeinate_pids_for(script.pid)), 1)

    def test_mac_is_actually_kept_awake(self):
        script = self.start()
        assertions = subprocess.run(
            ["pmset", "-g", "assertions"], capture_output=True, text=True
        ).stdout
        self.assertIn(f"on behalf of Process ID {script.pid}", assertions)

    def test_flags_are_passed_to_caffeinate(self):
        script = self.start("-i")
        result = subprocess.run(
            ["ps", "-o", "args=", "-p", str(caffeinate_pids_for(script.pid)[0])],
            capture_output=True, text=True,
        )
        self.assertEqual(result.stdout.strip(), f"caffeinate -i -w {script.pid}")

    def test_quit_keys_exit_cleanly_and_stop_caffeinate(self):
        for name, key in [("q", b"q"), ("Q", b"Q"), ("Esc", b"\x1b"), ("Ctrl-C", b"\x03")]:
            with self.subTest(key=name):
                script = self.start()
                script.send(key)
                self.assertEqual(script.wait(), 0)
                self.assertIn(b"caffeinate stopped.", script.output)
                self.assertTrue(wait_for_no_caffeinate(script.pid))

    def test_screen_turns_red_when_caffeinate_dies(self):
        script = self.start()
        os.kill(caffeinate_pids_for(script.pid)[0], signal.SIGTERM)
        self.assertTrue(script.read_until(b"STOPPED"), "status bar never showed STOPPED")
        self.assertTrue(script.read_until(b"caffeinate exited"))
        # The script keeps showing the red screen until you quit.
        script.send(b"q")
        self.assertEqual(script.wait(), 0)

    def test_force_killing_the_script_still_stops_caffeinate(self):
        script = self.start()
        os.kill(script.pid, signal.SIGKILL)
        self.assertEqual(script.wait(), -signal.SIGKILL)
        self.assertTrue(wait_for_no_caffeinate(script.pid), "caffeinate outlived the script")


class NoTerminalTest(unittest.TestCase):
    def test_refuses_to_run_when_output_is_not_a_terminal(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=10
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("needs an interactive terminal", result.stderr)


if __name__ == "__main__":
    unittest.main()
