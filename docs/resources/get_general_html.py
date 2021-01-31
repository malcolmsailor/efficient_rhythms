import os
import subprocess

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))

# Constants for processing general.md
GENERAL_MD_PATH = os.path.join(SCRIPT_DIR, "../general.md")
GENERAL_HTML_PATH = os.path.join(SCRIPT_DIR, "../general.html")

subprocess.run(
    ["pandoc", "-i", GENERAL_MD_PATH, "-o", GENERAL_HTML_PATH], check=True
)
