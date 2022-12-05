"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

import subprocess

class LoadingWindowHandler:
    """Create a seperate process to show a loading bar with indescriminate amount of time"""
    def __init__(self) -> None:
        self.process: subprocess.Popen = None
    
    def show(self, text: str):
        if self.process != None:
            self.kill()
        print(".\\loading\\loading_window.py " + '\"' + text + '\"')
        self.process = subprocess.Popen(
            ".\\loading\\loading_window.py " + '\"' + text + '\"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    
    def kill(self):
        subprocess.call(
            ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
            stdout=subprocess.DEVNULL,
        )

        self.process = None