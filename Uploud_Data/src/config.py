# config.py
# Konfigurasi proyek BIM Flight System

import os

# Dapatkan root folder proyek (folder bim-flight-demo)
# __file__ adalah path ke file config.py di folder src
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path ke credentials.json (gunakan path absolut)
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, "credentials", "credentials.json")

# Google Sheet Key
GOOGLE_SHEET_KEY = "1njLUn55TWwYjTQKEmmR97bcwgYaLYdF-0j5vK-vUIRw"

# Nama sheet
SHEET_RAW_ARRIVAL = "RAW_ARRIVAL"
SHEET_RAW_DEPARTURE = "RAW_DEPARTURE"
SHEET_LOG_UPLOAD = "LOG_UPLOAD"

# Folder data
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Untuk debugging
if __name__ == "__main__":
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"CREDENTIALS_PATH: {CREDENTIALS_PATH}")
    print(f"Credentials exists: {os.path.exists(CREDENTIALS_PATH)}")
