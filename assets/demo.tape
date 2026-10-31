# Records assets/demo.gif for the README using VHS
# (https://github.com/charmbracelet/vhs). From the repo root:
#
#   vhs assets/demo.tape
#
# Shows the green rain, then stops caffeinate so the red STOPPED screen appears.

Output assets/demo.gif

Set Shell "bash"
Set Theme "Builtin Dark"
Set FontSize 16
Set Width 960
Set Height 540
Set Padding 16
Set Framerate 20
Set TypingSpeed 60ms
Env LANG "en_US.UTF-8"

Hide
# Run this repo's copy of the script, and don't print job-control messages.
Type 'export PATH="$PWD:$PATH" PS1="$ "; set +m' Enter
# After a few seconds, stop the caffeinate started by this recording (and only
# that one: its -w pid must be a child of this shell), to show the red screen.
Type 'demo_shell=$$; (sleep 6.5; for c in $(pgrep -f "^caffeinate -ds -w "); do w=$(ps -o args= -p "$c" | awk "{print \$NF}"); [ "$(ps -o ppid= -p "$w" | tr -d " ")" = "$demo_shell" ] && kill "$c"; done) &' Enter
Type "clear" Enter
Show

Type "caffeinate-matrix"
Sleep 500ms
Enter
Sleep 8.5s

# Quit, which returns to the shell.
Type "q"
Sleep 2s
