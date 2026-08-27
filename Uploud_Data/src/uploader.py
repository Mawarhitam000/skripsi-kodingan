import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from config import CREDENTIALS_PATH, GOOGLE_SHEET_KEY, SHEET_RAW_ARRIVAL, SHEET_RAW_DEPARTURE, SHEET_LOG_UPLOAD

class FlightDataUploader:
    def __init__(self, credentials_path=CREDENTIALS_PATH, google_sheet_key=GOOGLE_SHEET_KEY):
        """Inisialisasi koneksi ke Google Sheets"""
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        self.gc = gspread.authorize(creds)
        self.sheet = self.gc.open_by_key(google_sheet_key)
        
        self.raw_arrival = self.sheet.worksheet(SHEET_RAW_ARRIVAL)
        self.raw_departure = self.sheet.worksheet(SHEET_RAW_DEPARTURE)
        self.log_upload = self.sheet.worksheet(SHEET_LOG_UPLOAD)

    def extract_tables(self, file_path):
        """Ekstrak 4 tabel menggunakan baris TOTAL sebagai boundary"""
        df_raw = pd.read_excel(file_path, sheet_name=0, header=None)
        
        total_rows = df_raw[df_raw[0].astype(str).str.contains('TOTAL', na=False)].index.tolist()
        
        if len(total_rows) < 3:
            raise ValueError("Format file tidak sesuai. Tidak menemukan cukup baris TOTAL.")
        
        tables = {
            'domestic_arrival': df_raw.iloc[6:total_rows[0]],
            'domestic_departure': df_raw.iloc[total_rows[0]+3:total_rows[1]],
            'international_arrival': df_raw.iloc[total_rows[1]+5:total_rows[2]],
            'international_departure': df_raw.iloc[total_rows[2]+3:total_rows[3] if len(total_rows)>3 else len(df_raw)]
        }
        
        # Bersihkan hanya baris yang memiliki Flight Number
        for key in tables:
            df = tables[key]
            valid = df[1].notna() & df[1].astype(str).str.contains(r'[A-Z]', na=False)
            # Buang header yang masih ikut
            header_keywords = 'FLIGHT|NO|CODE|NUMBER|ACFT|PAX|BLOCK|TAKE|OFF|REG|TYPE'
            cleaned = df[valid].copy()
            cleaned = cleaned[~cleaned[1].astype(str).str.contains(header_keywords, case=False, na=False)]
            tables[key] = cleaned.reset_index(drop=True)
            
        return tables

    def process_raw_table(self, df, table_type, data_date):
        """Mapping kolom sesuai struktur RAW_ARRIVAL / RAW_DEPARTURE (masih mentah)"""
        if df.empty:
            return pd.DataFrame()
        
        is_arrival = 'arrival' in table_type
        temp = pd.DataFrame()
        
        temp['Flight_Number'] = df.iloc[:, 1]
        temp['Paired_Flight'] = df.iloc[:, 2]
        temp['Aircraft_Reg'] = df.iloc[:, 3]
        temp['Aircraft_Type'] = df.iloc[:, 4]
        
        if is_arrival:
            temp['Origin'] = df.iloc[:, 5]
            temp['STA'] = df.iloc[:, 6]
            temp['Landing_Time'] = df.iloc[:, 7]
            temp['Onblock_Time'] = df.iloc[:, 8]
        else:
            temp['Destination'] = df.iloc[:, 5]
            temp['STD'] = df.iloc[:, 6]
            temp['BlockOff_Time'] = df.iloc[:, 7]
            temp['TakeOff_Time'] = df.iloc[:, 8]
        
        # Kolom bersama (mulai dari index 9)
        temp['Stand'] = df.iloc[:, 9] if df.shape[1] > 9 else None
        temp['AVB'] = df.iloc[:, 10] if df.shape[1] > 10 else None
        temp['Adult_Pax'] = df.iloc[:, 11] if df.shape[1] > 11 else 0
        temp['Child_Pax'] = df.iloc[:, 12] if df.shape[1] > 12 else 0
        temp['Infant_Pax'] = df.iloc[:, 13] if df.shape[1] > 13 else 0
        temp['Transit'] = df.iloc[:, 14] if df.shape[1] > 14 else 0
        temp['Total_Pax'] = df.iloc[:, 15] if df.shape[1] > 15 else 0
        temp['Seat'] = df.iloc[:, 16] if df.shape[1] > 16 else 0
        temp['Cargo_Kg'] = df.iloc[:, 17] if df.shape[1] > 17 else 0
        temp['Baggage_Kg'] = df.iloc[:, 18] if df.shape[1] > 18 else 0
        
        # Kolom tracking
        temp['Data_Date'] = data_date
        temp['Table_Type'] = table_type
        
        return temp

    def convert_to_serializable(self, df):
        """Konversi semua data di DataFrame ke format yang bisa di-serialize JSON"""
        df_clean = df.copy()
        
        for col in df_clean.columns:
            # Konversi semua data ke string
            df_clean[col] = df_clean[col].apply(lambda x: self._safe_convert(x))
        
        return df_clean

    def _safe_convert(self, value):
        """Konversi nilai ke format yang bisa di-serialize"""
        if pd.isna(value):
            return ""
        elif isinstance(value, (datetime, pd.Timestamp)):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        elif hasattr(value, 'strftime'):  # Untuk tipe time
            return value.strftime("%H:%M:%S")
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return str(value)

    def upload_file(self, file_path, data_date):
        """Fungsi utama untuk upload satu file Excel ke Google Sheets"""
        print(f"\nMengupload file: {os.path.basename(file_path)}")
        
        tables = self.extract_tables(file_path)
        
        arrival_dfs = []
        departure_dfs = []
        
        for table_type, df in tables.items():
            processed = self.process_raw_table(df, table_type, data_date)
            if processed.empty:
                continue
            if 'arrival' in table_type:
                arrival_dfs.append(processed)
            else:
                departure_dfs.append(processed)
        
        df_arrival = pd.concat(arrival_dfs, ignore_index=True) if arrival_dfs else pd.DataFrame()
        df_departure = pd.concat(departure_dfs, ignore_index=True) if departure_dfs else pd.DataFrame()
        
        # Konversi ke format yang bisa di-serialize
        if not df_arrival.empty:
            df_arrival_clean = self.convert_to_serializable(df_arrival)
            # Convert ke list of lists
            data_to_upload = df_arrival_clean.fillna("").values.tolist()
            # Upload ke Google Sheets (append)
            self.raw_arrival.append_rows(data_to_upload)
            print(f"✅ Berhasil upload {len(df_arrival)} baris ke RAW_ARRIVAL")
        
        if not df_departure.empty:
            df_departure_clean = self.convert_to_serializable(df_departure)
            data_to_upload = df_departure_clean.fillna("").values.tolist()
            self.raw_departure.append_rows(data_to_upload)
            print(f"✅ Berhasil upload {len(df_departure)} baris ke RAW_DEPARTURE")
        
        # Catat ke LOG_UPLOAD
        log_data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data_date,
            str(len(df_arrival)),
            str(len(df_departure)),
            "Success",
            os.path.basename(file_path)
        ]
        self.log_upload.append_row(log_data)
        print("✅ Log berhasil dicatat ke LOG_UPLOAD")
        
        return len(df_arrival), len(df_departure)