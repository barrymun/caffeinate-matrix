"""Fast tests for the script's logic. These never start caffeinate."""

import curses
import io
import os
import random
import subprocess
import unittest
from unittest import mock

from support import load_script

cm = load_script()


class TTYOutput(io.StringIO):
    def isatty(self):
        return True


class FormatUptimeTest(unittest.TestCase):
    def test_formats_hours_minutes_seconds(self):
        self.assertEqual(cm.format_uptime(0), "00:00:00")
        self.assertEqual(cm.format_uptime(59.9), "00:00:59")
        self.assertEqual(cm.format_uptime(3661), "01:01:01")

    def test_hours_keep_counting_past_a_day(self):
        self.assertEqual(cm.format_uptime(100 * 3600), "100:00:00")


class DropTest(unittest.TestCase):
    def setUp(self):
        random.seed(1234)

    def test_new_drop_starts_above_the_screen(self):
        for _ in range(200):
            drop = cm.Drop(40)
            self.assertTrue(-40 <= drop.y <= 0)
            self.assertTrue(0.3 <= drop.speed <= 1.0)
            self.assertTrue(5 <= drop.length <= 20)

    def test_tiny_terminal_still_gets_a_valid_length(self):
        for _ in range(50):
            self.assertIn(cm.Drop(3).length, (5, 6))

    def test_step_moves_down_by_speed(self):
        drop = cm.Drop(40)
        drop.y, drop.speed, drop.length = 0.0, 0.5, 10
        drop.step(40)
        self.assertEqual(drop.y, 0.5)

    def test_resets_once_the_tail_leaves_the_screen(self):
        drop = cm.Drop(40)
        drop.y, drop.speed, drop.length = 50.0, 1.0, 10  # tail at 41 after the step
        drop.step(40)
        self.assertTrue(-20 <= drop.y <= 0)


class SafeAddstrTest(unittest.TestCase):
    def test_swallows_curses_errors(self):
        win = mock.Mock()
        win.addstr.side_effect = curses.error
        cm.safe_addstr(win, 0, 0, "x")  # must not raise
        win.addstr.assert_called_once_with(0, 0, "x", 0)


class StartCaffeinateTest(unittest.TestCase):
    def test_passes_flags_and_waits_on_our_pid(self):
        with mock.patch.object(cm.subprocess, "Popen") as popen:
            cm.start_caffeinate(["-d", "-i"])
        args = popen.call_args[0][0]
        self.assertEqual(args, ["caffeinate", "-d", "-i", "-w", str(os.getpid())])


class MainTest(unittest.TestCase):
    def run_main(self, argv, proc=None, wrapper_error=None, stdout=None):
        proc = proc or mock.Mock(**{"poll.return_value": None})
        stdout = stdout if stdout is not None else TTYOutput()
        with mock.patch.object(cm.sys, "argv", ["caffeinate-matrix", *argv]), \
                mock.patch.object(cm.sys, "stdout", stdout), \
                mock.patch.object(cm.sys, "stderr", io.StringIO()) as stderr, \
                mock.patch.object(cm.locale, "setlocale"), \
                mock.patch.object(cm, "start_caffeinate", return_value=proc) as start, \
                mock.patch.object(cm.curses, "wrapper", side_effect=wrapper_error) as wrapper:
            code = cm.main()
        return code, start, wrapper, proc, stdout.getvalue(), stderr.getvalue()

    def test_defaults_to_ds(self):
        _, start, wrapper, proc, _, _ = self.run_main([])
        start.assert_called_once_with(["-ds"])
        wrapper.assert_called_once_with(cm.run, proc, ["-ds"])

    def test_passes_custom_flags_through(self):
        _, start, _, _, _, _ = self.run_main(["-dims"])
        start.assert_called_once_with(["-dims"])

    def test_help_prints_usage_without_starting_caffeinate(self):
        code, start, _, _, out, _ = self.run_main(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("Usage:", out)
        start.assert_not_called()

    def test_refuses_to_run_without_a_terminal(self):
        code, start, _, _, _, err = self.run_main([], stdout=io.StringIO())
        self.assertEqual(code, 1)
        self.assertIn("needs an interactive terminal", err)
        start.assert_not_called()

    def test_ctrl_c_stops_caffeinate(self):
        code, _, _, proc, out, _ = self.run_main([], wrapper_error=KeyboardInterrupt)
        self.assertEqual(code, 0)
        proc.terminate.assert_called_once()
        self.assertIn("caffeinate stopped.", out)

    def test_kills_caffeinate_if_it_ignores_terminate(self):
        proc = mock.Mock(**{"poll.return_value": None})
        proc.wait.side_effect = subprocess.TimeoutExpired("caffeinate", 2)
        self.run_main([], proc=proc)
        proc.terminate.assert_called_once()
        proc.kill.assert_called_once()

    def test_leaves_an_already_exited_caffeinate_alone(self):
        proc = mock.Mock(**{"poll.return_value": 0})
        self.run_main([], proc=proc)
        proc.terminate.assert_not_called()

    def test_stops_caffeinate_even_if_the_ui_crashes(self):
        proc = mock.Mock(**{"poll.return_value": None})
        with self.assertRaises(RuntimeError):
            self.run_main([], proc=proc, wrapper_error=RuntimeError("boom"))
        proc.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
