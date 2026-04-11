import sys
import os
import streamlit as st

# 1. Force the subdirectory into the Python path
sub_path = os.path.join(os.getcwd(), "inference_interface")
if sub_path not in sys.path:
    sys.path.append(sub_path)

# 2. Import the actual app logic from your subdirectory
try:
    # This assumes your v3.4 code is named app.py inside /inference_interface/
    from inference_interface.app import main
    main()
except ImportError:
    # Fallback if your v3.4 doesn't have a main() function wrapper
    import inference_interface.app