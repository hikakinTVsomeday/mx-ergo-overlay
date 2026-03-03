import sys
import traceback
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
    
    import main
    app = main.GestureOverlayApp()
    app.run()
except Exception as e:
    with open("crash.log", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())
