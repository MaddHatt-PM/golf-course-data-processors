import os


selfpath = os.path.abspath(__file__)
selfdir = os.path.dirname(selfpath)
os.chdir(selfdir)

import editor
