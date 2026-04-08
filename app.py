import sys
import os

# Ensures the subdirectory is in the system path for module and data discovery
sys.path.append(os.path.join(os.getcwd(), "inference_interface"))

# Executes the production app logic
with open("inference_interface/app.py") as f:
    code = compile(f.read(), "inference_interface/app.py", 'exec')
    exec(code, globals())