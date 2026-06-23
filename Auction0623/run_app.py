import sys
import os

# Set environment variable for protobuf
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
# Disable UPB C extension to prevent Python 3.14 TypeError
sys.modules['google._upb._message'] = None

from streamlit.web import cli as stcli

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(stcli.main())
