import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import calendar
from collections import defaultdict
import os
from fuzzywuzzy import fuzz
import io
import base64

class ExpenseAnalytics:
    def __init__(self, sheets_manager):
        self.sheets = sheets_manager
        
    def get_expenses_dataframe(self):
        """Convert sheet data to pandas DataFrame for analysis with robust header handling"""
        try:
            if not self.sheets.sheet:
                return None
            
            # Get all values as raw data to avoid header issues
            all_values = self.sheets.sheet.get_all_values()
            
            if not all_values:
                return None
            
            print(f"Got {len(all_values)} rows from sheet")
            
            # Find the actual header row by looking for key columns
            header_row_index = None
            data_start_index = None
            
            for i, row in enumerate(all_values):
                if len(row) >= 3:  # Need at least 3 columns
                    row_text = ' '.join(str(cell).lower() for cell in row)
                    # Look for header indicators
                    if any(keyword in row_text for keyword in ['date', 'amount', 'store', 'merchant', 'category']):
                        header_row_index = i
                        data_start_index = i + 1
                        print(f"Found headers at row {i+1}: {row}")
                        break
            
            # If no clear headers found, assume first row is headers or create them
            if header_row_index is None:
                print("No clear headers found, using default headers")
                headers = ['Date', 'Store/Merchant', 'Amount', 'Category', 'Payment Method', 'Notes', 'Receipt Date', 'Added Date']
                data_start_index = 0
            else:
                headers = all_values[header_row_index]
            
            # Get data rows
            if data_start_index < len(all_values):
                data_rows = all_values[data_start_index:]
            else:
                print("No data rows found after headers")
                return None
            
            # Filter out empty rows
            data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
            
            if not data_rows:
                print("No valid data rows found")
                return None
            
            print(f"Processing {len(data_rows)} data rows")
            
            # Create DataFrame
            records = []
            for row_idx, row in enumerate(data_rows):
                record = {}
                for col_idx, header in enumerate(headers):
                    if col_idx < len(row):
                        record[header] = row[col_idx]
                    else:
                        record[header] = ""
                
                # Only add records that have some data
                if any(str(value).strip() for value in record.values()):
                    records.append(record)
            
            if not records:
                print("No valid records created")
                return None
            
            df = pd.DataFrame(records)
            print(f"Created DataFrame with columns: {list(df.columns)}")
            
            # Find and clean amount column
            amount_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if 'amount' in col_lower:
                    amount_col = col
                    break
            
            if not amount_col:
                # Try to find numeric column
                for col in df.columns:
                    try:
                        numeric_values = pd.to_numeric(df[col], errors='coerce')
                        if numeric_values.notna().sum() > 0:
                            amount_col = col
                            print(f"Found numeric column for amount: {col}")
                            break
                    except:
                        continue
            
            if amount_col:
                # Clean amount data (remove various currency symbols)
                df['Amount'] = df[amount_col].astype(str).str.replace(',', '').str.replace('₱', '').str.replace('PHP', '').str.replace('P', '').str.replace('$', '')
                df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
                print(f"Processed amount column: {amount_col}")
            else:
                print("Warning: No amount column found")
                return None
            
            # Find and clean date column
            date_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if 'date' in col_lower and 'added' not in col_lower and 'receipt' not in col_lower:
                    date_col = col
                    break
            
            if date_col:
                df['Date'] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
                print(f"Processed date column: {date_col}")
            else:
                # Try to find any date-like column
                for col in df.columns:
                    try:
                        temp_dates = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                        if temp_dates.notna().sum() > 0:
                            df['Date'] = temp_dates
                            print(f"Found date-like column: {col}")
                            break
                    except:
                        continue
            
            # Find category column
            category_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if 'category' in col_lower:
                    category_col = col
                    df['Category'] = df[category_col]
                    break
            
            # Find merchant column
            merchant_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['store', 'merchant', 'vendor']):
                    merchant_col = col
                    df['Store/Merchant'] = df[merchant_col]
                    break
            
            # Filter out invalid data
            initial_count = len(df)
            df = df.dropna(subset=['Amount'])
            df = df[df['Amount'] > 0]
            
            if 'Date' in df.columns:
                df = df.dropna(subset=['Date'])
            
            final_count = len(df)
            print(f"Filtered from {initial_count} to {final_count} valid records")
            
            if df.empty:
                print("No valid data found after filtering")
                return None
            
            print(f"✅ Successfully loaded {len(df)} expense records")
            print(f"Date range: {df['Date'].min()} to {df['Date'].max()}" if 'Date' in df.columns else "No date information")
            print(f"Total amount: ₱{df['Amount'].sum():.2f}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error creating DataFrame: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_monthly_summary(self):
        """Generate monthly spending summary in PHP"""
        df = self.get_expenses_dataframe()
        
        if df is None or df.empty:
            return "📊 No expense data available for analysis."
        
        # Check if we have required columns
        if 'Amount' not in df.columns:
            return "📊 Amount data not found in the sheet."
        
        # Current month data
        if 'Date' in df.columns:
            current_month = datetime.now().replace(day=1)
            monthly_data = df[df['Date'] >= current_month]
            print(f"Current month filter: {current_month}")
            print(f"Monthly data count: {len(monthly_data)}")
            
            if monthly_data.empty:
                # Try current year instead
                current_year = datetime.now().year
                yearly_data = df[df['Date'].dt.year == current_year]
                if not yearly_data.empty:
                    monthly_data = yearly_data
                    print(f"Using yearly data instead: {len(monthly_data)} records")
                else:
                    # Use all data if no current year data
                    monthly_data = df
                    print(f"Using all data: {len(monthly_data)} records")
        else:
            # If no date column, use all data
            monthly_data = df
            print(f"No date column, using all data: {len(monthly_data)} records")
        
        if monthly_data.empty:
            return "📊 No expenses found in your sheet."
        
        # Calculate totals
        total_spent = monthly_data['Amount'].sum()
        num_transactions = len(monthly_data)
        avg_transaction = monthly_data['Amount'].mean()
        
        print(f"Calculations: Total=₱{total_spent:.2f}, Count={num_transactions}, Avg=₱{avg_transaction:.2f}")
        
        # Category breakdown (if category column exists)
        if 'Category' in monthly_data.columns:
            category_totals = monthly_data.groupby('Category')['Amount'].sum().sort_values(ascending=False)
        else:
            category_totals = pd.Series(dtype=float)
        
        # Top merchants (try different column names)
        merchant_col = None
        for col in monthly_data.columns:
            if any(word in col.lower() for word in ['store', 'merchant', 'vendor']):
                merchant_col = col
                break
        
        if merchant_col:
            merchant_totals = monthly_data.groupby(merchant_col)['Amount'].sum().sort_values(ascending=False).head(5)
        else:
            merchant_totals = pd.Series(dtype=float)
        
        # Generate report
        month_name = calendar.month_name[datetime.now().month]
        
        report = f"📊 **{month_name} {datetime.now().year} Summary**\n\n"
        report += f"💰 **Total Spent:** ₱{total_spent:,.2f}\n"
        report += f"🔢 **Transactions:** {num_transactions}\n"
        report += f"📊 **Average per Transaction:** ₱{avg_transaction:,.2f}\n\n"
        
        if not category_totals.empty:
            report += "🏷️ **By Category:**\n"
            for category, amount in category_totals.head(5).items():
                percentage = (amount / total_spent) * 100
                report += f"• {category}: ₱{amount:,.2f} ({percentage:.1f}%)\n"
        
        if not merchant_totals.empty:
            report += "\n🏪 **Top Merchants:**\n"
            for merchant, amount in merchant_totals.items():
                report += f"• {merchant}: ₱{amount:,.2f}\n"
        
        return report
    
    def detect_duplicates(self, new_expense):
        """Detect potential duplicate receipts with improved logic"""
        df = self.get_expenses_dataframe()
        
        if df is None or df.empty:
            return False, "No duplicates found - first expense!"
        
        if 'Amount' not in df.columns:
            return False, "Cannot check duplicates - missing amount data"
        
        new_amount = new_expense.get('total_amount', 0)
        new_merchant = new_expense.get('merchant', '').lower().strip()
        
        print(f"Checking for duplicates: ₱{new_amount:.2f} at '{new_merchant}'")
        
        # Check for duplicates within last 30 days (increased from 7)
        if 'Date' in df.columns:
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_expenses = df[df['Date'] >= thirty_days_ago]
            print(f"Checking against {len(recent_expenses)} recent expenses")
        else:
            # If no date column, check last 20 records
            recent_expenses = df.tail(20)
            print(f"No date column, checking last {len(recent_expenses)} records")
        
        # Find merchant column
        merchant_col = None
        for col in df.columns:
            if any(word in col.lower() for word in ['store', 'merchant', 'vendor']):
                merchant_col = col
                break
        
        duplicates_found = []
        
        for idx, expense in recent_expenses.iterrows():
            # Check amount similarity (within ₱10 - tighter tolerance)
            amount_diff = abs(expense['Amount'] - new_amount)
            
            # Get merchant from expense
            expense_merchant = ""
            if merchant_col and merchant_col in expense:
                expense_merchant = str(expense[merchant_col]).lower().strip()
            
            # Check for exact amount match OR very close amount (within ₱5)
            amount_match = (amount_diff <= 5.0)
            
            # Check merchant similarity
            merchant_similarity = 0
            if new_merchant and expense_merchant:
                merchant_similarity = fuzz.ratio(expense_merchant, new_merchant)
            
            # More strict duplicate detection logic
            is_duplicate = False
            match_reason = ""
            
            if amount_diff == 0 and merchant_similarity >= 70:
                # Exact amount + similar merchant = likely duplicate
                is_duplicate = True
                match_reason = "Exact amount + similar merchant"
            elif amount_diff <= 2.0 and merchant_similarity >= 85:
                # Very close amount + very similar merchant = likely duplicate  
                is_duplicate = True
                match_reason = "Very close amount + very similar merchant"
            elif amount_diff == 0 and (not new_merchant or not expense_merchant):
                # Exact amount but missing merchant info = possible duplicate
                is_duplicate = True
                match_reason = "Exact amount (merchant info missing)"
            
            if is_duplicate:
                expense_date = expense['Date'].strftime('%Y-%m-%d %H:%M') if 'Date' in expense else 'Unknown date'
                duplicate_info = {
                    'amount': expense['Amount'],
                    'merchant': expense_merchant or 'Unknown',
                    'date': expense_date,
                    'reason': match_reason,
                    'similarity': merchant_similarity
                }
                duplicates_found.append(duplicate_info)
                
                print(f"DUPLICATE FOUND: {match_reason} - ₱{expense['Amount']} at '{expense_merchant}' on {expense_date}")
        
        if duplicates_found:
            # Return the most likely duplicate (highest similarity)
            best_match = max(duplicates_found, key=lambda x: x['similarity'])
            
            message = f"⚠️ Possible duplicate receipt found!\n\n"
            message += f"**New Receipt:** ₱{new_amount:.2f} at {new_merchant or 'Unknown'}\n"
            message += f"**Existing:** ₱{best_match['amount']:.2f} at {best_match['merchant']} on {best_match['date']}\n"
            message += f"**Reason:** {best_match['reason']}\n"
            
            if len(duplicates_found) > 1:
                message += f"**Note:** Found {len(duplicates_found)} similar receipts"
            
            return True, message
        
        return False, "No duplicates detected"
    
    def generate_spending_chart(self, chart_type='category'):
        """Generate spending charts with PHP currency"""
        df = self.get_expenses_dataframe()
        
        if df is None or df.empty:
            return None
        
        # Set style
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == 'category':
            # Category pie chart
            if 'Category' not in df.columns:
                # Create a simple chart showing we need category data
                ax.text(0.5, 0.5, 'Category data not available\nin your sheet', 
                       ha='center', va='center', fontsize=16)
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_title('Category Breakdown')
            else:
                category_totals = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
                
                colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0', '#ffb3e6']
                
                # Format labels with PHP currency
                labels = [f"{cat}\n₱{amt:,.0f}" for cat, amt in category_totals.items()]
                
                ax.pie(category_totals.values, labels=labels, autopct='%1.1f%%', 
                       colors=colors[:len(category_totals)], startangle=90)
                ax.set_title('Spending by Category (PHP)', fontsize=16, fontweight='bold')
            
        elif chart_type == 'monthly':
            # Monthly spending trend
            if 'Date' not in df.columns:
                ax.text(0.5, 0.5, 'Date data not available\nin your sheet', 
                       ha='center', va='center', fontsize=16)
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_title('Monthly Trend')
            else:
                df['YearMonth'] = df['Date'].dt.to_period('M')
                monthly_totals = df.groupby('YearMonth')['Amount'].sum()
                
                ax.plot(range(len(monthly_totals)), monthly_totals.values, marker='o', linewidth=2, markersize=8)
                ax.set_xlabel('Month')
                ax.set_ylabel('Amount Spent (₱)')
                ax.set_title('Monthly Spending Trend (PHP)', fontsize=16, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                # Format y-axis with PHP currency
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₱{x:,.0f}'))
                
                # Set x-axis labels
                ax.set_xticks(range(len(monthly_totals)))
                ax.set_xticklabels([str(period) for period in monthly_totals.index], rotation=45)
        
        plt.tight_layout()
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        
        plt.close()  # Close the figure to free memory
        
        return img_buffer
    
    def get_budget_status(self, monthly_budget):
        """Check budget status for current month in PHP"""
        df = self.get_expenses_dataframe()
        
        if df is None or df.empty or 'Amount' not in df.columns:
            return {
                'status': "📊 No data yet",
                'budget': monthly_budget,
                'spent': 0,
                'remaining': monthly_budget,
                'percentage': 0
            }
        
        # Current month spending
        if 'Date' in df.columns:
            # Get current month properly
            now = datetime.now()
            current_month_start = now.replace(day=1)
            
            # Filter for current month
            monthly_data = df[df['Date'] >= current_month_start]
            
            # If no current month data, use all data as fallback
            if monthly_data.empty:
                print(f"No current month data found, using all data ({len(df)} records)")
                monthly_data = df
            else:
                print(f"Found {len(monthly_data)} expenses in current month")
        else:
            print("No date column, using all data")
            monthly_data = df
        
        spent = monthly_data['Amount'].sum() if not monthly_data.empty else 0
        remaining = monthly_budget - spent
        percentage_used = (spent / monthly_budget) * 100 if monthly_budget > 0 else 0
        
        print(f"Budget calculation: Spent=₱{spent:.2f}, Budget=₱{monthly_budget:.2f}, Percentage={percentage_used:.1f}%")
        
        # Budget status
        if percentage_used >= 100:
            status = "🚨 OVER BUDGET!"
        elif percentage_used >= 80:
            status = "⚠️ Approaching Limit"
        elif percentage_used >= 60:
            status = "📊 On Track"
        else:
            status = "✅ Under Budget"
        
        return {
            'status': status,
            'budget': monthly_budget,
            'spent': spent,
            'remaining': remaining,
            'percentage': percentage_used
        }
    
    def get_category_insights(self):
        """Generate spending insights by category in PHP"""
        df = self.get_expenses_dataframe()
        
        if df is None or df.empty:
            return "📊 No data available for insights."
        
        if 'Amount' not in df.columns:
            return "📊 Missing amount data for insights."
        
        insights = []
        
        # Category spending this month vs last month (if we have date and category data)
        if 'Date' in df.columns and 'Category' in df.columns:
            current_month = datetime.now().replace(day=1)
            last_month = (current_month - timedelta(days=1)).replace(day=1)
            
            current_data = df[df['Date'] >= current_month].groupby('Category')['Amount'].sum()
            last_month_data = df[(df['Date'] >= last_month) & (df['Date'] < current_month)].groupby('Category')['Amount'].sum()
            
            for category in current_data.index:
                current_amount = current_data[category]
                last_amount = last_month_data.get(category, 0)
                
                if last_amount > 0:
                    change = ((current_amount - last_amount) / last_amount) * 100
                    if abs(change) > 20:  # Significant change
                        direction = "📈 increased" if change > 0 else "📉 decreased"
                        insights.append(f"• {category} {direction} by {abs(change):.1f}% from last month")
        
        # Add total spending insight
        total_spent = df['Amount'].sum()
        insights.append(f"• Total spending across all records: ₱{total_spent:,.2f}")
        
        if 'Date' in df.columns:
            date_range = f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}"
            insights.append(f"• Data covers period: {date_range}")
        
        if not insights:
            insights.append("• Spending patterns are consistent with last month")
        
        return "\n".join(insights)