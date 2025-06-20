import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re
import json
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsConnector:
    def __init__(self, credentials_dict):
        """Initialize with credentials dictionary"""
        self.creds_dict = credentials_dict
        self.client = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            # Define scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            # Create credentials from dict
            creds = Credentials.from_service_account_info(
                self.creds_dict,
                scopes=scopes
            )
            
            # Authorize client
            self.client = gspread.authorize(creds)
            logger.info("Successfully authenticated with Google Sheets")
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise Exception(f"Failed to authenticate: {str(e)}")
    
    def extract_sheet_id(self, url):
        """Extract sheet ID from URL"""
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'^([a-zA-Z0-9-_]+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Invalid Google Sheets URL")
    
    def connect(self, sheet_url, worksheet_name=None):
        """Connect to sheet and return data"""
        try:
            # Extract sheet ID
            sheet_id = self.extract_sheet_id(sheet_url)
            
            # Open spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            
            # Get worksheet
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.sheet1
            
            # Get all data
            data = worksheet.get_all_values()
            
            if not data:
                return pd.DataFrame()
            
            # Create DataFrame
            headers = data[0]
            rows = data[1:]
            
            df = pd.DataFrame(rows, columns=headers)
            
            # Clean data types
            df = self._clean_data(df)
            
            return df
            
        except gspread.exceptions.SpreadsheetNotFound:
            raise Exception("Spreadsheet not found. Make sure it's shared with the service account!")
        except Exception as e:
            raise Exception(f"Connection error: {str(e)}")
    
    def _clean_data(self, df):
        """Clean and convert data types"""
        # Remove empty columns/rows
        df = df.loc[:, (df != '').any(axis=0)]
        df = df[(df != '').any(axis=1)]
        
        # Convert numeric columns
        for col in df.columns:
            try:
                # Try to convert to numeric
                numeric_data = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')
                if numeric_data.notna().sum() > len(df) * 0.5:
                    df[col] = numeric_data
            except:
                pass
        
        return df