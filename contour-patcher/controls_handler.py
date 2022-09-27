import subprocess
import modes


class ControlsHandler:
    def __init__(s, cv2_title) -> None:
        s.mode = modes.M_DEFAULT
        s.controls_win: subprocess.Popen = None
        s.cv2_title = cv2_title
        s.switch_to(s.mode)

    def changeWindowName(s, title: str):
        s.cv2_title = title

    def switch_to(s, mode: str):
        if s.controls_win is not None:
            s.kill()

        s.controls_win = subprocess.Popen(
            "controls_subprocess.py " + mode,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def kill(s):
        subprocess.call(
            ["taskkill", "/F", "/T", "/PID", str(s.controls_win.pid)],
            stdout=subprocess.DEVNULL,
        )
