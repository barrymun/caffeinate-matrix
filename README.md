# caffeinate-matrix

Runs `caffeinate -ds` with Matrix-style digital rain in the terminal, so you can
tell at a glance that your Mac is being kept awake.

```bash
./caffeinate-matrix          # same as: caffeinate -ds
./caffeinate-matrix -dims    # any caffeinate flags are passed straight through
```

Press `q`, `Esc` or `Ctrl-C` to quit. Quitting also stops caffeinate.

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
- To run it from anywhere, symlink it into a directory on your `PATH` that you
  own, e.g. `ln -s "$PWD/caffeinate-matrix" ~/.local/bin/caffeinate-matrix`
  (`/usr/local/bin` works too, but needs `sudo`).

## Credits

The rain effect was inspired by the
[Matrix effect script](https://github.com/zero-to-mastery/ascii-art/blob/master/ascii-art-matrix-effect.py)
in zero-to-mastery's [ascii-art](https://github.com/zero-to-mastery/ascii-art) repo.

## License

[MIT](LICENSE)
