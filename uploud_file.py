"""
Demo Upload Data Mentah dengan File Picker (Command Line)
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog

# Tambahkan path src
SRC_PATH = os.path.join(os.path.dirname(__file__), 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from uploader import FlightDataUploader
from config import CREDENTIALS_PATH, GOOGLE_SHEET_KEY, DATA_DIR

def select_file_gui():
    """Buka file dialog untuk memilih file"""
    root = tk.Tk()
    root.withdraw()  # Sembunyikan window utama
    
    initial_dir = os.path.join(DATA_DIR, "februari")
    if not os.path.exists(initial_dir):
        initial_dir = DATA_DIR
    
    file_path = filedialog.askopenfilename(
        title="Pilih File Excel",
        initialdir=initial_dir,
        filetypes=[
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*")
        ]
    )
    
    root.destroy()
    return file_path

def main():
    print("="*60)
    print("BIM FLIGHT SYSTEM - UPLOAD DATA MENTAH")
    print("="*60)
    
    # Inisialisasi uploader
    try:
        uploader = FlightDataUploader(CREDENTIALS_PATH, GOOGLE_SHEET_KEY)
        print("✅ Berhasil terhubung ke Google Sheets")
    except Exception as e:
        print(f"❌ Gagal terhubung: {e}")
        return
    
    # Pilih file dengan dialog
    print("\n📂 Membuka dialog pilih file...")
    file_path = select_file_gui()
    
    if not file_path:
        print("❌ Tidak ada file dipilih")
        return
    
    print(f"✅ File dipilih: {os.path.basename(file_path)}")
    
    # Input tanggal
    data_date = input("Masukkan tanggal data (YYYY-MM-DD): ").strip()
    
    # Upload
    try:
        total_arr, total_dep = uploader.upload_file(file_path, data_date)
        print("\n" + "="*60)
        print("🎉 UPLOAD BERHASIL!")
        print(f"   Total Arrival   : {total_arr} baris")
        print(f"   Total Departure : {total_dep} baris")
        print("="*60)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()