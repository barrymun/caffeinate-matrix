# caffeinate-matrix

[![CI](https://github.com/barrymun/caffeinate-matrix/actions/workflows/tests.yml/badge.svg)](https://github.com/barrymun/caffeinate-matrix/actions/workflows/tests.yml)

Runs `caffeinate -ds` with Matrix-style digital rain in the terminal, so you can
tell at a glance that your Mac is being kept awake.

![caffeinate-matrix running: green Matrix rain with an ACTIVE status bar, then a red STOPPED screen once caffeinate exits](assets/demo.gif)

```bash
./caffeinate-matrix          # same as: caffeinate -ds
./caffeinate-matrix -dims    # any caffeinate flags are passed straight through
```

Press `q`, `Esc` or `Ctrl-C` to quit. Quitting also stops caffeinate.

## Running it from anywhere

Symlink the script into a directory on your `PATH`. From inside the cloned repo:

```bash
mkdir -p ~/.local/bin
ln -s "$PWD/caffeinate-matrix" ~/.local/bin/caffeinate-matrix
```

You can then run `caffeinate-matrix` from any directory (open a new terminal tab,
or run `rehash` in zsh, if it isn't found straight away).

If `~/.local/bin` isn't on your `PATH`, add this line to your `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

To uninstall, remove the link:

```bash
rm ~/.local/bin/caffeinate-matrix
```

- `/usr/local/bin` also works, but needs `sudo`.
- Because it's a symlink, changes to the repo take effect immediately, and
  `git pull` keeps it up to date. If you move or rename the repo folder,
  remove the link and create it again.

## What you see

- **Green rain + green status bar** (`ACTIVE`, pid, uptime): caffeinate is running.
- **Frozen red rain + red status bar** (`STOPPED`): caffeinate has exited, so your
  Mac can sleep again.

The rain follows the real caffeinate process rather than just the script, so a
moving screen really does mean caffeinate is running.

## Notes

- Uses only the Python 3 standard library (the macOS system `python3` is enough).
- caffeinate is started with `-w <script pid>`, so it exits along with the script
  even if the terminal is closed or the script is force-killed. No stray
  caffeinate is left running.
- `-s` (prevent system sleep) only takes effect on AC power. That's how
  caffeinate itself works.

## Testing

The tests use only the standard library. From the repo root:

```bash
python3 -m unittest discover -s tests -v
```

- `tests/test_unit.py` covers the script's logic without starting caffeinate.
- `tests/test_end_to_end.py` runs the real script in a pseudo-terminal: it checks
  the rain and status bar, that the Mac is really kept awake, the quit keys, the
  red `STOPPED` screen, and that no caffeinate is left behind. These tests only
  run on macOS and keep your Mac awake for a few seconds while they run.

To run only the unit tests (instant, and they never start caffeinate):

```bash
python3 -m unittest discover -s tests -p 'test_unit.py' -v
```

To run only the tests whose names match a word, e.g. `quit`:

```bash
python3 -m unittest discover -s tests -v -k quit
```

GitHub Actions runs the full suite on macOS on every push and pull request,
with both the macOS system Python and the latest Python.

## Linting

CI also checks the code with [Ruff](https://docs.astral.sh/ruff/), using the
settings in `ruff.toml`. Ruff isn't needed to run or test the script.

To run the same checks locally, install the Ruff version CI uses (pinned in
`.github/workflows/tests.yml`, so your results match CI):

```bash
brew install pipx
```

```bash
pipx install ruff==0.17.3
```

Check for lint problems and formatting differences:

```bash
ruff check . && ruff format --check .
```

Fix what Ruff can fix automatically, then reformat:

```bash
ruff check --fix . && ruff format .
```

## Updating the preview

The GIF at the top is recorded with [VHS](https://github.com/charmbracelet/vhs)
from the script in `assets/demo.tape`. To re-record it after changing the
script, install VHS:

```bash
brew install vhs
```

Then, from the repo root:

```bash
vhs assets/demo.tape
```

Recording runs caffeinate for about 10 seconds. The demo only stops the
caffeinate it started itself, so any other caffeinate-matrix you have running
is left alone.

## Credits

The rain effect was inspired by the
[Matrix effect script](https://github.com/zero-to-mastery/ascii-art/blob/master/ascii-art-matrix-effect.py)
in zero-to-mastery's [ascii-art](https://github.com/zero-to-mastery/ascii-art) repo.

## License

[MIT](LICENSE)
