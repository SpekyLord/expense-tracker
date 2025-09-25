import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime
import json

class ExpenseSheets:
    def __init__(self):
        try:
            # Setup Google Sheets connection
            credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
            
            if not os.path.exists(credentials_file):
                print("❌ Google credentials file not found!")
                self.client = None
                return
            
            # Define the required scopes
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Authenticate and create client
            creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
            self.client = gspread.authorize(creds)
            self.sheet = None
            print("✅ Google Sheets connection ready!")
            
        except Exception as e:
            print(f"❌ Error setting up Google Sheets: {e}")
            self.client = None
    
    def fix_sheet_headers(self):
        """Fix corrupted sheet headers"""
        try:
            if not self.sheet:
                return False
            
            # Get all values
            all_values = self.sheet.get_all_values()
            if not all_values:
                return False
            
            # Check if first row has proper headers
            first_row = all_values[0]
            expected_headers = ['Date', 'Store/Merchant', 'Amount', 'Category', 
                              'Payment Method', 'Notes', 'Receipt Date', 'Added Date']
            
            # If first row doesn't look like headers, we need to fix it
            if not any(header.lower() in str(first_row).lower() for header in ['date', 'amount', 'store', 'merchant']):
                print("🔧 Fixing sheet headers...")
                
                # Insert proper headers at the top
                self.sheet.insert_row(expected_headers, 1)
                
                # Format header row
                self.sheet.format('A1:H1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                })
                
                print("✅ Headers fixed!")
                return True
            else:
                print("✅ Headers look correct")
                return True
                
        except Exception as e:
            print(f"❌ Error fixing headers: {e}")
            return False
    
    def create_expense_sheet(self, sheet_name="My Expense Tracker"):
        """Create a new Google Sheet for expenses"""
        try:
            if not self.client:
                return None
            
            # Create new spreadsheet
            spreadsheet = self.client.create(sheet_name)
            
            # Setup the main worksheet
            worksheet = spreadsheet.sheet1
            worksheet.update('A1:H1', [[
                'Date', 'Store/Merchant', 'Amount', 'Category', 
                'Payment Method', 'Notes', 'Receipt Date', 'Added Date'
            ]])
            
            # Format header row
            worksheet.format('A1:H1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            self.sheet = worksheet
            sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
            
            print(f"✅ Created new expense sheet: {sheet_url}")
            return sheet_url
            
        except Exception as e:
            print(f"❌ Error creating sheet: {e}")
            return None
    
    def connect_to_existing_sheet(self, sheet_url):
        """Connect to an existing Google Sheet with header validation"""
        try:
            if not self.client:
                return False
            
            # Extract sheet ID from URL
            if '/spreadsheets/d/' in sheet_url:
                sheet_id = sheet_url.split('/spreadsheets/d/')[1].split('/')[0]
            else:
                sheet_id = sheet_url
            
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            self.sheet = spreadsheet.sheet1
            
            print(f"🔗 Connected to sheet: {sheet_id}")
            
            # Try to fix headers if needed
            self.fix_sheet_headers()
            
            print(f"✅ Successfully connected and validated!")
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to sheet: {e}")
            return False
    
    def validate_sheet_structure(self):
        """Validate that the sheet has the correct structure"""
        try:
            if not self.sheet:
                return False
            
            # Get first row
            first_row = self.sheet.row_values(1)
            
            # Check if we have basic required headers
            required_headers = ['date', 'amount']  # Minimum required
            
            first_row_lower = [str(cell).lower() for cell in first_row]
            
            has_required = all(
                any(req in cell for cell in first_row_lower) 
                for req in required_headers
            )
            
            if not has_required:
                print("⚠️ Sheet structure may need adjustment")
                return self.fix_sheet_headers()
            
            return True
            
        except Exception as e:
            print(f"❌ Error validating sheet structure: {e}")
            return False
    
    def add_expense(self, expense_data):
        """Add an expense to the Google Sheet with better error handling"""
        try:
            if not self.sheet:
                print("❌ No sheet connected!")
                return False
            
            # Validate sheet structure first
            if not self.validate_sheet_structure():
                print("❌ Sheet structure validation failed")
                return False
            
            # Get current date for "Added Date"
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Use receipt date if found, otherwise use current date
            receipt_date = expense_data.get('date', 'Not found')
            if receipt_date == 'Not found' or receipt_date == 'Date not found':
                display_date = current_date  # Use today's date
                receipt_date = 'Not found on receipt'
            else:
                display_date = receipt_date
            
            # Prepare the row data
            row_data = [
                display_date,  # Date column (receipt date or today)
                expense_data.get('merchant', 'Unknown'),  # Store/Merchant
                expense_data.get('total_amount', 0),  # Amount
                expense_data.get('category', 'General'),  # Category
                expense_data.get('payment_method', 'Unknown'),  # Payment Method
                expense_data.get('notes', ''),  # Notes
                receipt_date,  # Receipt Date (what was found on receipt)
                current_time  # Added Date (when added to sheet)
            ]
            
            # Add the row to the sheet
            self.sheet.append_row(row_data)
            
            print(f"✅ Added expense to sheet: ₱{expense_data.get('total_amount', 0)} at {expense_data.get('merchant', 'Unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding expense to sheet: {e}")
            # Try to provide helpful error message
            if "PERMISSION_DENIED" in str(e):
                print("💡 Make sure the service account has edit permissions to your sheet")
            elif "INVALID_ARGUMENT" in str(e):
                print("💡 Check if your sheet has the correct column structure")
            return False
    
    def get_sheet_url(self):
        """Get the URL of the current sheet"""
        try:
            if self.sheet:
                return f"https://docs.google.com/spreadsheets/d/{self.sheet.spreadsheet.id}"
            return None
        except:
            return None
    
    def get_recent_expenses(self, limit=5):
        """Get recent expenses from the sheet with better error handling"""
        try:
            if not self.sheet:
                return []
            
            # Try to get all values first
            all_values = self.sheet.get_all_values()
            if not all_values or len(all_values) < 2:  # Need at least header + 1 data row
                return []
            
            # Get headers from first row
            headers = all_values[0]
            
            # Get data rows
            data_rows = all_values[1:]
            
            # Convert to records format
            records = []
            for row in data_rows[-limit:]:  # Get last 'limit' rows
                if len(row) >= 3:  # At least date, merchant, amount
                    record = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            record[header] = row[i]
                        else:
                            record[header] = ""
                    records.append(record)
            
            return records
            
        except Exception as e:
            print(f"❌ Error getting recent expenses: {e}")
            return []