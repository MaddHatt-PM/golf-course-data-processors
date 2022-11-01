import subprocess

class LoadingWindowHandler:
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