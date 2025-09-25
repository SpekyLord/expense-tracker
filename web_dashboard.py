from flask import Flask, render_template, jsonify
import json
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv

# Import your existing modules
from sheets_manager import ExpenseSheets
from analytics_engine import ExpenseAnalytics

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Initialize your components
sheets = ExpenseSheets()
analytics = ExpenseAnalytics(sheets)

# For demo purposes - you'll need to connect to a real sheet
DEMO_SHEET_URL = "your_sheet_url_here"  # Replace with actual sheet URL

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/summary')
def get_summary():
    """API endpoint for summary data"""
    try:
        # Connect to sheets (you'll need to modify this for your setup)
        # sheets.connect_to_existing_sheet(DEMO_SHEET_URL)
        
        # Get real data from your sheets
        df = analytics.get_expenses_dataframe()
        
        if df is not None and not df.empty:
            # Calculate real summary data
            current_month = datetime.now().replace(day=1)
            monthly_data = df[df['Date'] >= current_month]
            
            total_spent = monthly_data['Amount'].sum() if not monthly_data.empty else 0
            transactions = len(monthly_data) if not monthly_data.empty else 0
            avg_transaction = monthly_data['Amount'].mean() if not monthly_data.empty else 0
            
            # Category breakdown
            categories = {}
            if not monthly_data.empty:
                category_totals = monthly_data.groupby('Category')['Amount'].sum()
                categories = category_totals.to_dict()
            
            return jsonify({
                'total_spent': float(total_spent),
                'transactions': int(transactions),
                'avg_transaction': float(avg_transaction),
                'categories': categories
            })
        else:
            # Return demo data if no real data available
            return jsonify({
                'total_spent': 1247.50,
                'transactions': 45,
                'avg_transaction': 27.72,
                'categories': {
                    'Food & Dining': 450.00,
                    'Groceries': 320.00,
                    'Transportation': 180.00,
                    'Shopping': 297.50
                }
            })
            
    except Exception as e:
        print(f"Error in get_summary: {e}")
        # Return demo data on error
        return jsonify({
            'total_spent': 1247.50,
            'transactions': 45,
            'avg_transaction': 27.72,
            'categories': {
                'Food & Dining': 450.00,
                'Groceries': 320.00,
                'Transportation': 180.00,
                'Shopping': 297.50
            }
        })

@app.route('/api/chart/<chart_type>')
def get_chart_data(chart_type):
    """API endpoint for chart data"""
    try:
        df = analytics.get_expenses_dataframe()
        
        if df is not None and not df.empty:
            if chart_type == 'category':
                # Real category data
                category_totals = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
                
                return jsonify({
                    'labels': category_totals.index.tolist(),
                    'data': category_totals.values.tolist(),
                    'colors': ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0', '#ffb3e6'][:len(category_totals)]
                })
                
            elif chart_type == 'monthly':
                # Real monthly trend data
                df['YearMonth'] = df['Date'].dt.to_period('M')
                monthly_totals = df.groupby('YearMonth')['Amount'].sum()
                
                return jsonify({
                    'labels': [str(period) for period in monthly_totals.index],
                    'data': monthly_totals.values.tolist()
                })
        
        # Return demo data if no real data
        if chart_type == 'category':
            return jsonify({
                'labels': ['Food & Dining', 'Groceries', 'Transport', 'Shopping'],
                'data': [450, 320, 180, 297.50],
                'colors': ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
            })
        elif chart_type == 'monthly':
            return jsonify({
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
                'data': [1200, 1100, 1350, 980, 1247]
            })
            
    except Exception as e:
        print(f"Error in get_chart_data: {e}")
        # Return demo data on error
        if chart_type == 'category':
            return jsonify({
                'labels': ['Food & Dining', 'Groceries', 'Transport', 'Shopping'],
                'data': [450, 320, 180, 297.50],
                'colors': ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
            })
        elif chart_type == 'monthly':
            return jsonify({
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
                'data': [1200, 1100, 1350, 980, 1247]
            })

@app.route('/api/connect/<path:sheet_url>')
def connect_sheet(sheet_url):
    """Connect to a Google Sheet via web interface"""
    try:
        if sheets.connect_to_existing_sheet(sheet_url):
            return jsonify({'success': True, 'message': 'Connected to Google Sheet successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to connect to Google Sheet'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    print("🌐 Starting Web Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🔄 The dashboard will show demo data until you connect a Google Sheet")
    app.run(debug=True, port=5000)