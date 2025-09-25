import pandas as pd
from datetime import datetime, timedelta
import calendar
from fpdf import FPDF
import matplotlib.pyplot as plt
import seaborn as sns
import io
import os

class ReportGenerator:
    def __init__(self, analytics_engine):
        self.analytics = analytics_engine
        
    def generate_monthly_pdf_report(self, user_id):
        """Generate comprehensive PDF report"""
        df = self.analytics.get_expenses_dataframe()
        
        if df is None or df.empty:
            return None
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        current_month = datetime.now().strftime('%B %Y')
        pdf.cell(0, 10, f'Expense Report - {current_month}', 0, 1, 'C')
        pdf.ln(10)
        
        # Summary section
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Monthly Summary', 0, 1)
        pdf.set_font('Arial', '', 12)
        
        # Calculate summary stats
        current_month_data = df[df['Date'] >= datetime.now().replace(day=1)]
        total_spent = current_month_data['Amount'].sum()
        num_transactions = len(current_month_data)
        avg_transaction = current_month_data['Amount'].mean() if num_transactions > 0 else 0
        
        pdf.cell(0, 8, f'Total Spent: ₱{total_spent:.2f}', 0, 1)
        pdf.cell(0, 8, f'Number of Transactions: {num_transactions}', 0, 1)
        pdf.cell(0, 8, f'Average Transaction: ₱{avg_transaction:.2f}', 0, 1)
        pdf.ln(5)
        
        # Category breakdown
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Spending by Category', 0, 1)
        pdf.set_font('Arial', '', 12)
        
        category_totals = current_month_data.groupby('Category')['Amount'].sum().sort_values(ascending=False)
        
        for category, amount in category_totals.items():
            percentage = (amount / total_spent) * 100 if total_spent > 0 else 0
            pdf.cell(0, 8, f'{category}: ₱{amount:.2f} ({percentage:.1f}%)', 0, 1)
        
        # Save PDF
        pdf_filename = f"expense_report_{datetime.now().strftime('%Y_%m')}.pdf"
        pdf.output(pdf_filename)
        
        return pdf_filename
    
    def generate_yearly_summary(self):
        """Generate yearly spending summary"""
        df = self.analytics.get_expenses_dataframe()
        
        if df is None or df.empty:
            return "📊 No data available for yearly summary."
        
        current_year = datetime.now().year
        yearly_data = df[df['Date'].dt.year == current_year]
        
        if yearly_data.empty:
            return f"📊 No expenses recorded for {current_year} yet."
        
        total_spent = yearly_data['Amount'].sum()
        num_transactions = len(yearly_data)
        
        # Monthly breakdown
        monthly_totals = yearly_data.groupby(yearly_data['Date'].dt.month)['Amount'].sum()
        
        # Top categories
        category_totals = yearly_data.groupby('Category')['Amount'].sum().sort_values(ascending=False)
        
        # Generate report
        report = f"📅 **{current_year} Yearly Summary**\n\n"
        report += f"💰 **Total Spent:** ₱{total_spent:.2f}\n"
        report += f"📝 **Total Transactions:** {num_transactions}\n"
        report += f"📊 **Average per Month:** ₱{total_spent/12:.2f}\n\n"
        
        report += "📅 **Monthly Breakdown:**\n"
        for month_num, amount in monthly_totals.items():
            month_name = calendar.month_name[month_num]
            report += f"• {month_name}: ₱{amount:.2f}\n"
        
        report += "\n🏷️ **Top Categories:**\n"
        for category, amount in category_totals.head(5).items():
            percentage = (amount / total_spent) * 100
            report += f"• {category}: ₱{amount:.2f} ({percentage:.1f}%)\n"
        
        return report
    
    def generate_comparison_report(self, months_back=3):
        """Compare spending across recent months"""
        df = self.analytics.get_expenses_dataframe()
        
        if df is None or df.empty:
            return "📊 No data available for comparison."
        
        # Get data for last N months
        end_date = datetime.now().replace(day=1)
        start_date = end_date - timedelta(days=30*months_back)
        
        comparison_data = df[df['Date'] >= start_date]
        
        if comparison_data.empty:
            return f"📊 No data available for the last {months_back} months."
        
        # Group by month and category
        monthly_category = comparison_data.groupby([
            comparison_data['Date'].dt.to_period('M'),
            'Category'
        ])['Amount'].sum().unstack(fill_value=0)
        
        report = f"📊 **Last {months_back} Months Comparison**\n\n"
        
        for category in monthly_category.columns:
            report += f"🏷️ **{category}:**\n"
            for month, amount in monthly_category[category].items():
                report += f"  • {month}: ₱{amount:.2f}\n"
            report += "\n"
        
        return report

class SmartInsights:
    def __init__(self, analytics_engine):
        self.analytics = analytics_engine
    
    def get_spending_patterns(self):
        """Analyze spending patterns and provide insights"""
        df = self.analytics.get_expenses_dataframe()
        
        if df is None or df.empty:
            return ["📊 Not enough data for pattern analysis yet."]
        
        insights = []
        
        # Day of week analysis
        df['DayOfWeek'] = df['Date'].dt.day_name()
        daily_spending = df.groupby('DayOfWeek')['Amount'].sum()
        highest_spending_day = daily_spending.idxmax()
        
        insights.append(f"📅 You spend most on {highest_spending_day}s (₱{daily_spending[highest_spending_day]:.2f} average)")
        
        # Time of month analysis
        df['DayOfMonth'] = df['Date'].dt.day
        if df['DayOfMonth'].max() > 15:
            first_half = df[df['DayOfMonth'] <= 15]['Amount'].sum()
            second_half = df[df['DayOfMonth'] > 15]['Amount'].sum()
            
            if first_half > second_half * 1.2:
                insights.append("💡 You tend to spend more in the first half of the month")
            elif second_half > first_half * 1.2:
                insights.append("💡 You tend to spend more in the second half of the month")
        
        # Large transaction analysis
        avg_amount = df['Amount'].mean()
        large_transactions = df[df['Amount'] > avg_amount * 3]
        
        if len(large_transactions) > 0:
            insights.append(f"💰 You have {len(large_transactions)} transactions above ₱{avg_amount*3:.2f}")
        
        # Frequency analysis
        merchant_counts = df['Store/Merchant'].value_counts()
        if len(merchant_counts) > 0:
            most_frequent = merchant_counts.index[0]
            count = merchant_counts.iloc[0]
            insights.append(f"🏪 Most frequent merchant: {most_frequent} ({count} visits)")
        
        return insights
    
    def get_savings_suggestions(self):
        """Generate money-saving suggestions based on spending patterns"""
        df = self.analytics.get_expenses_dataframe()
        
        if df is None or df.empty:
            return ["💡 Start tracking expenses to get personalized savings suggestions!"]
        
        suggestions = []
        
        # Category-based suggestions
        current_month = datetime.now().replace(day=1)
        monthly_data = df[df['Date'] >= current_month]
        
        if not monthly_data.empty:
            category_totals = monthly_data.groupby('Category')['Amount'].sum().sort_values(ascending=False)
            
            # Food & Dining suggestions
            if 'Food & Dining' in category_totals and category_totals['Food & Dining'] > 300:
                suggestions.append("🍽️ Consider meal planning to reduce dining out expenses")
            
            # Transportation suggestions
            if 'Transportation' in category_totals and category_totals['Transportation'] > 200:
                suggestions.append("🚗 Look into carpooling or public transport to save on gas")
            
            # Shopping suggestions
            if 'Shopping' in category_totals and category_totals['Shopping'] > 500:
                suggestions.append("🛍️ Try the 24-hour rule before making non-essential purchases")
        
        # Frequency-based suggestions
        merchant_counts = df['Store/Merchant'].value_counts()
        if len(merchant_counts) > 0 and merchant_counts.iloc[0] > 10:
            suggestions.append(f"💳 Consider loyalty programs for {merchant_counts.index[0]}")
        
        if not suggestions:
            suggestions.append("✅ Your spending patterns look reasonable! Keep tracking for more insights.")
        
        return suggestions