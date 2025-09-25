import json
import os
from datetime import datetime, timedelta

class BudgetManager:
    def __init__(self):
        self.budget_file = "user_budgets.json"
        self.budgets = self.load_budgets()
    
    def load_budgets(self):
        """Load user budgets from file"""
        try:
            if os.path.exists(self.budget_file):
                with open(self.budget_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ Error loading budgets: {e}")
            return {}
    
    def save_budgets(self):
        """Save budgets to file"""
        try:
            with open(self.budget_file, 'w') as f:
                json.dump(self.budgets, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving budgets: {e}")
            return False
    
    def set_budget(self, user_id, category, amount, period='monthly'):
        """Set budget for user and category"""
        if user_id not in self.budgets:
            self.budgets[user_id] = {}
        
        if 'categories' not in self.budgets[user_id]:
            self.budgets[user_id]['categories'] = {}
        
        self.budgets[user_id]['categories'][category] = {
            'amount': float(amount),
            'period': period,
            'created': datetime.now().isoformat()
        }
        
        return self.save_budgets()
    
    def set_total_budget(self, user_id, amount, period='monthly'):
        """Set total monthly budget"""
        if user_id not in self.budgets:
            self.budgets[user_id] = {}
        
        self.budgets[user_id]['total'] = {
            'amount': float(amount),
            'period': period,
            'created': datetime.now().isoformat()
        }
        
        return self.save_budgets()
    
    def get_budget(self, user_id, category=None):
        """Get budget for user"""
        if user_id not in self.budgets:
            return None
        
        if category:
            return self.budgets[user_id].get('categories', {}).get(category)
        else:
            return self.budgets[user_id].get('total')
    
    def get_all_budgets(self, user_id):
        """Get all budgets for user"""
        return self.budgets.get(user_id, {})
    
    def check_budget_alerts(self, user_id, current_spending):
        """Check if user is approaching budget limits"""
        user_budgets = self.get_all_budgets(user_id)
        alerts = []
        
        # Check total budget
        total_budget = user_budgets.get('total')
        if total_budget and current_spending.get('total', 0) > 0:
            spent = current_spending['total']
            budget_amount = total_budget['amount']
            percentage = (spent / budget_amount) * 100
            
            if percentage >= 90:
                alerts.append(f"🚨 Total budget alert: {percentage:.1f}% used (₱{spent:.2f}/₱{budget_amount:.2f})")
            elif percentage >= 75:
                alerts.append(f"⚠️ Budget warning: {percentage:.1f}% used (₱{spent:.2f}/₱{budget_amount:.2f})")
        
        # Check category budgets
        category_budgets = user_budgets.get('categories', {})
        for category, budget_info in category_budgets.items():
            if category in current_spending:
                spent = current_spending[category]
                budget_amount = budget_info['amount']
                percentage = (spent / budget_amount) * 100
                
                if percentage >= 90:
                    alerts.append(f"🚨 {category} budget alert: {percentage:.1f}% used")
                elif percentage >= 75:
                    alerts.append(f"⚠️ {category} budget warning: {percentage:.1f}% used")
        
        return alerts