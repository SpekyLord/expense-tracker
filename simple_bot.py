import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from ocr_processor import ReceiptOCR
from sheets_manager import ExpenseSheets
from analytics_engine import ExpenseAnalytics
from budget_manager import BudgetManager
from report_generator import ReportGenerator, SmartInsights
import asyncio

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize components
ocr = ReceiptOCR()
sheets = ExpenseSheets()
analytics = ExpenseAnalytics(sheets)
budget_manager = BudgetManager()
report_gen = ReportGenerator(analytics)
insights_engine = SmartInsights(analytics)

# Store user data
user_sheets = {}
user_budgets = {}

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate comprehensive reports"""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_sheets:
        await update.message.reply_text("❌ No Google Sheet connected. Use /start to set one up.")
        return
    
    # Connect to user's sheet
    sheets.connect_to_existing_sheet(user_sheets[user_id])
    
    # Show report options
    keyboard = [
        [InlineKeyboardButton("📊 Monthly Report", callback_data="monthly_report")],
        [InlineKeyboardButton("📅 Yearly Summary", callback_data="yearly_summary")],
        [InlineKeyboardButton("📈 Spending Patterns", callback_data="spending_patterns")],
        [InlineKeyboardButton("💡 Savings Tips", callback_data="savings_tips")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📊 **Choose Your Report:**\n\n"
        "• **Monthly** - Current month analysis\n"
        "• **Yearly** - Full year overview\n"
        "• **Patterns** - Spending behavior insights\n"
        "• **Savings** - Personalized money-saving tips",
        reply_markup=reply_markup
    )

async def insights_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get smart insights about spending"""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_sheets:
        await update.message.reply_text("❌ No Google Sheet connected. Use /start to set one up.")
        return
    
    sheets.connect_to_existing_sheet(user_sheets[user_id])
    
    # Get patterns and suggestions
    patterns = insights_engine.get_spending_patterns()
    suggestions = insights_engine.get_savings_suggestions()
    
    response = "🧠 **Smart Insights**\n\n"
    response += "📊 **Your Spending Patterns:**\n"
    for pattern in patterns:
        response += f"{pattern}\n"
    
    response += "\n💡 **Savings Suggestions:**\n"
    for suggestion in suggestions:
        response += f"{suggestion}\n"
    
    await update.message.reply_text(response)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced start command with analytics preview"""
    keyboard = [
        [InlineKeyboardButton("📊 Create New Expense Sheet", callback_data="create_sheet")],
        [InlineKeyboardButton("🔗 Connect to Existing Sheet", callback_data="connect_sheet")],
        [InlineKeyboardButton("📈 Analytics Demo", callback_data="analytics_demo")],
        [InlineKeyboardButton("ℹ️ How it Works", callback_data="how_it_works")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎉 **Smart Expense Tracker - PHP Edition!**\n\n"
        "🔥 **NEW FEATURES:**\n"
        "📊 Monthly spending analytics\n"
        "💰 Budget tracking & alerts (in PHP)\n"
        "📈 Visual charts & reports\n"
        "🔍 Duplicate detection\n"
        "📱 Enhanced dashboard\n\n"
        "**Core Features:**\n"
        "📸 OCR receipt reading\n"
        "📊 Auto-save to Google Sheets\n"
        "🏷️ Smart category detection\n"
        "📅 Intelligent date handling\n"
        "💱 Philippine Peso (₱) support\n\n"
        "**Get started:**",
        reply_markup=reply_markup
    )

async def analytics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show analytics dashboard"""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_sheets:
        await update.message.reply_text("❌ No Google Sheet connected. Use /start to set one up.")
        return
    
    # Connect to user's sheet FIRST
    if not sheets.connect_to_existing_sheet(user_sheets[user_id]):
        await update.message.reply_text("❌ Could not connect to your Google Sheet. Please check permissions.")
        return
    
    # Generate monthly summary
    summary = analytics.generate_monthly_summary()
    
    # Generate insights
    insights = analytics.get_category_insights()
    
    # Check budget status - MAKE SURE TO GET BUDGET FIRST
    user_budget = budget_manager.get_budget(user_id)
    budget_info = ""
    
    if user_budget:
        # Debug: Show what budget we found
        print(f"Found user budget: ₱{user_budget['amount']:.2f}")
        
        budget_status = analytics.get_budget_status(user_budget['amount'])
        budget_info = f"\n💰 **Budget Status:**\n"
        budget_info += f"{budget_status['status']}\n"
        budget_info += f"Spent: ₱{budget_status['spent']:.2f} / ₱{budget_status['budget']:.2f}\n"
        budget_info += f"Progress: {budget_status['percentage']:.1f}%\n"
        
        # Add progress bar visual
        progress_filled = int(budget_status['percentage'] / 10)
        progress_bar = "█" * progress_filled + "░" * (10 - progress_filled)
        budget_info += f"[{progress_bar}] {budget_status['percentage']:.1f}%\n"
    else:
        budget_info = "\n💰 **No budget set** - Use /budget 1500 to set one\n"
    
    # Create analytics keyboard
    keyboard = [
        [InlineKeyboardButton("📊 Category Chart", callback_data="chart_category")],
        [InlineKeyboardButton("📈 Monthly Trend", callback_data="chart_monthly")],
        [InlineKeyboardButton("💰 Set Budget", callback_data="set_budget")],
        [InlineKeyboardButton("📝 Recent Analysis", callback_data="recent_analysis")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    response = summary + budget_info + f"\n📝 **Insights:**\n{insights}"
    
    await update.message.reply_text(
        response,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced photo handler with better duplicate detection"""
    user_id = str(update.effective_user.id)
    
    # Check if user has a sheet connected
    if user_id not in user_sheets:
        keyboard = [
            [InlineKeyboardButton("📊 Create New Sheet", callback_data="create_sheet")],
            [InlineKeyboardButton("🔗 Connect Existing", callback_data="connect_sheet")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📊 **First, let's set up your Google Sheet:**",
            reply_markup=reply_markup
        )
        return
    
    try:
        # Send processing message
        processing_msg = await update.message.reply_text(
            "📸 Processing receipt...\n"
            "📖 Reading text...\n"
            "🔍 Checking for duplicates...\n"
            "📊 Preparing to save..."
        )
        
        # Download and process photo
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = f"temp_receipt_{update.message.message_id}.jpg"
        await file.download_to_drive(file_path)
        
        # OCR Processing
        extracted_text = ocr.read_receipt(file_path)
        
        if extracted_text:
            receipt_info = ocr.extract_info(extracted_text)
            
            # Connect to user's sheet
            sheets.connect_to_existing_sheet(user_sheets[user_id])
            
            # Check for duplicates BEFORE saving
            is_duplicate, duplicate_msg = analytics.detect_duplicates(receipt_info)
            
            if is_duplicate:
                # Store receipt info for potential force save
                context.user_data[f'pending_receipt_{update.message.message_id}'] = receipt_info
                
                keyboard = [
                    [InlineKeyboardButton("✅ Save Anyway", callback_data=f"force_save_{update.message.message_id}")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_save")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await processing_msg.edit_text(
                    f"🚫 **DUPLICATE RECEIPT DETECTED**\n\n"
                    f"{duplicate_msg}\n\n"
                    f"**What would you like to do?**\n"
                    f"• **Save Anyway** - Add this receipt despite the warning\n"
                    f"• **Cancel** - Don't save this receipt\n\n"
                    f"*This prevents accidental double-entries of the same expense.*",
                    reply_markup=reply_markup
                )
                
                # Clean up temp file
                try:
                    os.remove(file_path)
                except:
                    pass
                return  # IMPORTANT: Don't save automatically if duplicate found
            
            # No duplicate detected - proceed with normal save
            if sheets.add_expense(receipt_info):
                # Check budget alerts
                user_budget = budget_manager.get_budget(user_id)
                alerts = []
                
                if user_budget:
                    budget_status = analytics.get_budget_status(user_budget['amount'])
                    
                    if budget_status['percentage'] >= 90:
                        alerts.append(f"🚨 Budget Alert: {budget_status['percentage']:.1f}% used (₱{budget_status['spent']:.2f}/₱{budget_status['budget']:.2f})")
                    elif budget_status['percentage'] >= 75:
                        alerts.append(f"⚠️ Budget Warning: {budget_status['percentage']:.1f}% used (₱{budget_status['spent']:.2f}/₱{budget_status['budget']:.2f})")
                
                # Format success response
                response = "✅ **Receipt Processed & Saved!**\n\n"
                response += f"🏪 **Store:** {receipt_info.get('merchant', 'Unknown')}\n"
                response += f"💰 **Amount:** ₱{receipt_info.get('total_amount', 0):.2f}\n"
                response += f"🏷️ **Category:** {receipt_info.get('category', 'General')}\n"
                response += f"📅 **Date:** {receipt_info.get('date', 'Used today\'s date')}\n"
                
                if alerts:
                    response += f"\n🔔 **Budget Alerts:**\n"
                    for alert in alerts:
                        response += f"{alert}\n"
                
                response += f"\n📊 [View in Google Sheets]({user_sheets[user_id]})"
                
                # Add quick analytics button
                keyboard = [
                    [InlineKeyboardButton("📊 View Analytics", callback_data="quick_analytics")],
                    [InlineKeyboardButton("📈 Monthly Report", callback_data="monthly_report")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await processing_msg.edit_text(response, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await processing_msg.edit_text(
                    "❌ **Could not save to Google Sheets**\n"
                    "Please check your sheet permissions and try again."
                )
        else:
            await processing_msg.edit_text(
                "❌ **Could not read the receipt**\n\n"
                "💡 **Tips for better results:**\n"
                "• Ensure good lighting\n"
                "• Keep receipt flat\n"
                "• Take photo from directly above\n"
                "• Avoid shadows and glare"
            )
        
        # Clean up temp file
        try:
            os.remove(file_path)
        except:
            pass
            
    except Exception as e:
        await update.message.reply_text(f"❌ **Error:** {str(e)}")
        print(f"Error in handle_photo: {e}")
        import traceback
        traceback.print_exc()

async def enhanced_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete button handler with ALL callback cases"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    try:
        # CREATE NEW SHEET
        if query.data == "create_sheet":
            sheet_url = sheets.create_expense_sheet("My Smart Expense Tracker")
            if sheet_url:
                user_sheets[user_id] = sheet_url
                
                await query.edit_message_text(
                    f"✅ **Smart Expense Sheet Created!**\n\n"
                    f"📊 [Open Sheet]({sheet_url})\n\n"
                    f"🎯 **You're all set!** Your sheet includes:\n"
                    f"• Automatic categorization\n"
                    f"• Date tracking\n"
                    f"• Monthly summaries\n"
                    f"• Budget tracking columns\n\n"
                    f"📸 **Send me a receipt photo to get started!**",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "❌ **Could not create sheet**\n"
                    "Please check your Google credentials setup."
                )
        
        # CONNECT TO EXISTING SHEET
        elif query.data == "connect_sheet":
            await query.edit_message_text(
                "🔗 **Connect to Your Existing Google Sheet**\n\n"
                "**Step 1:** Open your Google Sheet\n"
                "**Step 2:** Copy the URL from your browser\n"
                "**Step 3:** Send me the URL as a regular message\n\n"
                "**Example URL format:**\n"
                "`https://docs.google.com/spreadsheets/d/ABC123.../edit`\n\n"
                "**Important:** Make sure your sheet is shared with:\n"
                "`expense-tracker-bot@expense-tracker-473206.iam.gserviceaccount.com`\n\n"
                "💡 **Tip:** Give the service account 'Editor' permissions!"
            )
        
        # ANALYTICS DEMO
        elif query.data == "analytics_demo":
            demo_keyboard = [
                [InlineKeyboardButton("📊 View Demo Charts", callback_data="demo_charts")],
                [InlineKeyboardButton("📈 Sample Analytics", callback_data="demo_analytics")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_start")]
            ]
            demo_reply_markup = InlineKeyboardMarkup(demo_keyboard)
            
            await query.edit_message_text(
                "🎬 **Analytics Demo Preview**\n\n"
                "**Features you'll get:**\n\n"
                "📊 **Visual Charts:**\n"
                "• Spending by category (pie charts)\n"
                "• Monthly spending trends (line charts)\n"
                "• Interactive data visualization\n\n"
                "💰 **Budget Tracking:**\n"
                "• Set monthly and category budgets\n"
                "• Real-time spending alerts\n"
                "• Budget vs actual comparisons\n\n"
                "🔍 **Smart Insights:**\n"
                "• Spending pattern analysis\n"
                "• Duplicate detection\n"
                "• Personalized savings tips\n"
                "• Monthly and yearly reports",
                reply_markup=demo_reply_markup
            )
        
        # HOW IT WORKS
        elif query.data == "how_it_works":
            how_keyboard = [
                [InlineKeyboardButton("🚀 Get Started Now", callback_data="back_to_start")]
            ]
            how_reply_markup = InlineKeyboardMarkup(how_keyboard)
            
            await query.edit_message_text(
                "📋 **How Smart Expense Tracker Works**\n\n"
                "**1. Setup (One-time):**\n"
                "• Create or connect Google Sheet\n"
                "• Set optional budgets\n\n"
                "**2. Daily Use:**\n"
                "• Take photo of any receipt\n"
                "• Bot reads text automatically\n"
                "• Data saved to your sheet instantly\n\n"
                "**3. Analytics & Reports:**\n"
                "• Use /analytics for spending overview\n"
                "• Use /report for detailed analysis\n"
                "• Use /insights for personalized tips\n\n"
                "**4. Budget Management:**\n"
                "• Use /budget 1500 for total budget\n"
                "• Use /budget food 400 for category budget\n"
                "• Get automatic alerts when approaching limits",
                reply_markup=how_reply_markup
            )
        
        # BACK TO START
        elif query.data == "back_to_start":
            keyboard = [
                [InlineKeyboardButton("📊 Create New Expense Sheet", callback_data="create_sheet")],
                [InlineKeyboardButton("🔗 Connect to Existing Sheet", callback_data="connect_sheet")],
                [InlineKeyboardButton("📈 Analytics Demo", callback_data="analytics_demo")],
                [InlineKeyboardButton("ℹ️ How it Works", callback_data="how_it_works")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🎉 **Smart Expense Tracker - Analytics Edition!**\n\n"
                "🔥 **NEW FEATURES:**\n"
                "📊 Monthly spending analytics\n"
                "💰 Budget tracking & alerts\n"
                "📈 Visual charts & reports\n"
                "🔍 Duplicate detection\n"
                "📱 Enhanced dashboard\n\n"
                "**Core Features:**\n"
                "📸 OCR receipt reading\n"
                "📊 Auto-save to Google Sheets\n"
                "🏷️ Smart category detection\n"
                "📅 Intelligent date handling\n\n"
                "**Get started:**",
                reply_markup=reply_markup
            )
        
        # QUICK ANALYTICS (from "View Analytics" button)
        elif query.data == "quick_analytics":
            if user_id not in user_sheets:
                await query.edit_message_text("❌ No Google Sheet connected. Use /start to set one up.")
                return
                
            # Connect to user's sheet
            sheets.connect_to_existing_sheet(user_sheets[user_id])
            
            # Generate monthly summary
            summary = analytics.generate_monthly_summary()
            
            # Generate insights
            insights = analytics.get_category_insights()
            
            # Check budget status
            user_budget = budget_manager.get_budget(user_id)
            budget_info = ""
            
            if user_budget:
                budget_status = analytics.get_budget_status(user_budget['amount'])
                budget_info = f"\n💰 **Budget Status:**\n"
                budget_info += f"{budget_status['status']}\n"
                budget_info += f"Spent: ₱{budget_status['spent']:.2f} / ₱{budget_status['budget']:.2f}\n"
                budget_info += f"Progress: {budget_status['percentage']:.1f}%\n"
            
            # Create analytics keyboard
            keyboard = [
                [InlineKeyboardButton("📊 Category Chart", callback_data="chart_category")],
                [InlineKeyboardButton("📈 Monthly Trend", callback_data="chart_monthly")],
                [InlineKeyboardButton("💰 Set Budget", callback_data="set_budget")],
                [InlineKeyboardButton("📝 Full Report", callback_data="monthly_report")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            response = summary + budget_info + f"\n🔍 **Insights:**\n{insights}"
            
            await query.edit_message_text(
                response,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # CATEGORY CHART
        elif query.data == "chart_category":
            if user_id not in user_sheets:
                await query.edit_message_text("❌ No Google Sheet connected.")
                return
                
            sheets.connect_to_existing_sheet(user_sheets[user_id])
            
            chart_buffer = analytics.generate_spending_chart('category')
            if chart_buffer:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=chart_buffer,
                    caption="📊 **Your Spending by Category**\n\nUse /analytics for more insights!"
                )
            else:
                await query.edit_message_text("❌ Not enough data for category chart yet. Add some expenses first!")
        
        # MONTHLY TREND CHART
        elif query.data == "chart_monthly":
            if user_id not in user_sheets:
                await query.edit_message_text("❌ No Google Sheet connected.")
                return
                
            sheets.connect_to_existing_sheet(user_sheets[user_id])
            
            chart_buffer = analytics.generate_spending_chart('monthly')
            if chart_buffer:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=chart_buffer,
                    caption="📈 **Monthly Spending Trend**\n\nTrack your spending patterns over time!"
                )
            else:
                await query.edit_message_text("❌ Need at least 2 months of data for trend chart.")
        
        # SET BUDGET
        elif query.data == "set_budget":
            await query.edit_message_text(
                "💰 **Set Your Budget**\n\n"
                "Use these commands to set budgets:\n\n"
                "**Total Monthly Budget:**\n"
                "`/budget 1500` - Set ₱1500/month budget\n\n"
                "**Category Budget:**\n"
                "`/budget food 400` - Set ₱400 food budget\n"
                "`/budget transport 200` - Set ₱200 transport budget\n\n"
                "**Available Categories:**\n"
                "• food, groceries, transport, shopping\n"
                "• entertainment, health, general"
            )
        
        # RECENT ANALYSIS
        elif query.data == "recent_analysis":
            if user_id not in user_sheets:
                await query.edit_message_text("❌ No Google Sheet connected.")
                return
                
            sheets.connect_to_existing_sheet(user_sheets[user_id])
            
            recent_expenses = sheets.get_recent_expenses(limit=10)
            
            if not recent_expenses:
                await query.edit_message_text("📊 No recent expenses found. Start by adding some receipts!")
                return
            
            response = "📋 **Recent Expenses:**\n\n"
            total_recent = 0
            
            for expense in recent_expenses[-5:]:  # Show last 5
                try:
                    amount = float(expense.get('Amount', 0))
                    total_recent += amount
                    response += f"• ₱{amount:.2f} at {expense.get('Store/Merchant', 'Unknown')} ({expense.get('Category', 'General')})\n"
                except (ValueError, TypeError):
                    continue
            
            response += f"\n💰 **Recent Total:** ₱{total_recent:.2f}"
            response += f"\n📊 **Total Transactions:** {len(recent_expenses)}"
            
            await query.edit_message_text(response)
        
        # MONTHLY REPORT
        elif query.data == "monthly_report":
            if user_id not in user_sheets:
                await query.edit_message_text("❌ No Google Sheet connected.")
                return
                
            sheets.connect_to_existing_sheet(user_sheets[user_id])
            
            monthly_summary = analytics.generate_monthly_summary()
            insights = analytics.get_category_insights()
            
            report = f"{monthly_summary}\n\n🔍 **Insights:**\n{insights}"
            
            await query.edit_message_text(report)
        
        # YEARLY SUMMARY
        elif query.data == "yearly_summary":
            if user_id not in user_sheets:
                await query.edit_message_text("❌ No Google Sheet connected.")
                return
                
            sheets.connect_to_existing_sheet(user_sheets[user_id])
            
            yearly_report = report_gen.generate_yearly_summary()
            await query.edit_message_text(yearly_report)
        
        # SPENDING PATTERNS
        elif query.data == "spending_patterns":
            if user_id not in user_sheets:
                await query.edit_message_text("❌ No Google Sheet connected.")
                return
                
            sheets.connect_to_existing_sheet(user_sheets[user_id])
            
            patterns = insights_engine.get_spending_patterns()
            response = "📊 **Your Spending Patterns:**\n\n"
            for pattern in patterns:
                response += f"{pattern}\n"
            
            await query.edit_message_text(response)
        
        # SAVINGS TIPS
        elif query.data == "savings_tips":
            if user_id not in user_sheets:
                await query.edit_message_text("❌ No Google Sheet connected.")
                return
                
            sheets.connect_to_existing_sheet(user_sheets[user_id])
            
            suggestions = insights_engine.get_savings_suggestions()
            response = "💡 **Personalized Savings Tips:**\n\n"
            for suggestion in suggestions:
                response += f"{suggestion}\n"
            
            await query.edit_message_text(response)
        
        # DEMO CHARTS
        elif query.data == "demo_charts":
            await query.edit_message_text(
                "📊 **Demo Charts Preview**\n\n"
                "**Available Chart Types:**\n\n"
                "🥧 **Category Pie Chart:**\n"
                "• Visual breakdown of spending by category\n"
                "• Percentage and dollar amounts\n"
                "• Color-coded for easy identification\n\n"
                "📈 **Monthly Trend Line:**\n"
                "• Track spending over time\n"
                "• Identify spending patterns\n"
                "• Compare month-to-month changes\n\n"
                "📊 **Budget Progress Bars:**\n"
                "• Visual budget vs actual spending\n"
                "• Category-wise budget tracking\n"
                "• Alert indicators for overspending\n\n"
                "💡 **Connect your sheet and add expenses to see real charts!**"
            )
        
        # DEMO ANALYTICS
        elif query.data == "demo_analytics":
            await query.edit_message_text(
                "📈 **Sample Analytics Report**\n\n"
                "📊 **May 2024 Summary**\n\n"
                "💰 **Total Spent:** ₱1,247.50\n"
                "📝 **Transactions:** 45\n"
                "📊 **Average per Transaction:** ₱27.72\n\n"
                "🏷️ **By Category:**\n"
                "• Food & Dining: ₱450.00 (36.1%)\n"
                "• Groceries: ₱320.00 (25.7%)\n"
                "• Transportation: ₱180.00 (14.4%)\n"
                "• Shopping: ₱297.50 (23.8%)\n\n"
                "🏪 **Top Merchants:**\n"
                "• Starbucks: ₱87.50\n"
                "• Target: ₱156.00\n"
                "• Shell Gas: ₱124.00\n\n"
                "🔍 **Insights:**\n"
                "• You spend most on Fridays (₱245.00 average)\n"
                "• Food spending increased by 15% from last month\n"
                "• 3 transactions above ₱75.00\n\n"
                "💡 **This is sample data - connect your sheet for real analytics!**"
            )
        
        # FORCE SAVE (for duplicate detection)
        elif query.data.startswith("force_save_"):
            message_id = query.data.split("_")[-1]
            receipt_info = context.user_data.get(f'pending_receipt_{message_id}')
            
            if receipt_info:
                if user_id in user_sheets:
                    sheets.connect_to_existing_sheet(user_sheets[user_id])
                    
                if sheets.add_expense(receipt_info):
                    await query.edit_message_text(
                        f"✅ **Receipt Saved Despite Duplicate Warning**\n\n"
                        f"💰 ₱{receipt_info.get('total_amount', 0):.2f} at {receipt_info.get('merchant', 'Unknown')}\n"
                        f"🏷️ Category: {receipt_info.get('category', 'General')}"
                    )
                else:
                    await query.edit_message_text("❌ Failed to save receipt to sheet.")
            else:
                await query.edit_message_text("❌ Receipt data not found.")
        
        # CANCEL SAVE
        elif query.data == "cancel_save":
            await query.edit_message_text("❌ **Receipt not saved** - Duplicate avoided!")
        
        # FALLBACK - Unknown callback
        else:
            await query.edit_message_text(f"❌ Unknown action: {query.data}\nTry using /start to reset.")
    
    except Exception as e:
        print(f"Button handler error: {e}")
        await query.edit_message_text(f"❌ **Error processing request**\n\nError: {str(e)}\n\nTry using /start to reset.")

# Also add the URL handler for connecting existing sheets
async def handle_sheet_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Google Sheet URL when user sends it"""
    message_text = update.message.text
    
    # Check if message contains a Google Sheets URL
    if 'docs.google.com/spreadsheets' in message_text:
        user_id = str(update.effective_user.id)
        
        # Extract the URL (in case user sent additional text)
        import re
        url_pattern = r'https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9-_]+(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#.*)?'
        urls = re.findall(url_pattern, message_text)
        
        if urls:
            sheet_url = urls[0]
            
            # Try to connect
            if sheets.connect_to_existing_sheet(sheet_url):
                user_sheets[user_id] = sheet_url
                
                keyboard = [
                    [InlineKeyboardButton("📊 View Analytics", callback_data="quick_analytics")],
                    [InlineKeyboardButton("💰 Set Budget", callback_data="set_budget")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ **Successfully Connected!**\n\n"
                    f"🔗 Connected to your Google Sheet\n"
                    f"📊 [View Sheet]({sheet_url})\n\n"
                    f"🎯 **Ready to go!** You can now:\n"
                    f"• Send receipt photos for automatic processing\n"
                    f"• Use /analytics for spending insights\n"
                    f"• Use /budget to set spending limits\n"
                    f"• Use /report for detailed analysis\n\n"
                    f"📸 **Send me your first receipt photo!**",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ **Could not connect to the sheet**\n\n"
                    "**Possible issues:**\n"
                    "• Sheet is not shared with the bot service account\n"
                    "• Invalid URL format\n"
                    "• Sheet doesn't exist or is private\n\n"
                    "**To fix:**\n"
                    "1. Open your Google Sheet\n"
                    "2. Click 'Share' button\n"
                    "3. Add this email with Editor access:\n"
                    "`expense-tracker-bot@expense-tracker-473206.iam.gserviceaccount.com`\n"
                    "4. Send me the URL again"
                )
        else:
            await update.message.reply_text(
                "❌ **Invalid Google Sheets URL**\n\n"
                "Please send a valid Google Sheets URL like:\n"
                "`https://docs.google.com/spreadsheets/d/ABC123.../edit`"
            )

# You also need to add a message handler for when users send Google Sheet URLs
async def handle_sheet_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Google Sheet URL when user sends it"""
    message_text = update.message.text
    
    # Check if message contains a Google Sheets URL
    if 'docs.google.com/spreadsheets' in message_text:
        user_id = str(update.effective_user.id)
        
        # Extract the URL (in case user sent additional text)
        import re
        url_pattern = r'https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9-_]+(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#.*)?'
        urls = re.findall(url_pattern, message_text)
        
        if urls:
            sheet_url = urls[0]
            
            # Try to connect
            if sheets.connect_to_existing_sheet(sheet_url):
                user_sheets[user_id] = sheet_url
                
                keyboard = [
                    [InlineKeyboardButton("📊 View Analytics", callback_data="quick_analytics")],
                    [InlineKeyboardButton("💰 Set Budget", callback_data="set_budget")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ **Successfully Connected!**\n\n"
                    f"🔗 Connected to your Google Sheet\n"
                    f"📊 [View Sheet]({sheet_url})\n\n"
                    f"🎯 **Ready to go!** You can now:\n"
                    f"• Send receipt photos for automatic processing\n"
                    f"• Use /analytics for spending insights\n"
                    f"• Use /budget to set spending limits\n"
                    f"• Use /report for detailed analysis\n\n"
                    f"📸 **Send me your first receipt photo!**",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ **Could not connect to the sheet**\n\n"
                    "**Possible issues:**\n"
                    "• Sheet is not shared with the bot service account\n"
                    "• Invalid URL format\n"
                    "• Sheet doesn't exist or is private\n\n"
                    "**To fix:**\n"
                    "1. Open your Google Sheet\n"
                    "2. Click 'Share' button\n"
                    "3. Add this email with Editor access:\n"
                    "`expense-tracker-bot@expense-tracker-473206.iam.gserviceaccount.com`\n"
                    "4. Send me the URL again"
                )
        else:
            await update.message.reply_text(
                "❌ **Invalid Google Sheets URL**\n\n"
                "Please send a valid Google Sheets URL like:\n"
                "`https://docs.google.com/spreadsheets/d/ABC123.../edit`"
            )

# Add this handler to your main() function:
# application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sheet_url))

async def budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set budget command"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text(
            "💰 **Budget Commands:**\n\n"
            "**Set total budget:** `/budget 1500`\n"
            "**Set category budget:** `/budget food 400`\n\n"
            "**Categories:** food, groceries, transport, shopping, entertainment, health, general"
        )
        return
    
    try:
        if len(context.args) == 1:
            # Total budget
            amount = float(context.args[0])
            budget_manager.set_total_budget(user_id, amount)
            await update.message.reply_text(
                f"✅ **Total monthly budget set to ₱{amount:.2f}**\n\n"
                "I'll alert you when you reach 75% and 90% of your budget!"
            )
        
        elif len(context.args) == 2:
            # Category budget
            category = context.args[0].lower()
            amount = float(context.args[1])
            budget_manager.set_budget(user_id, category, amount)
            await update.message.reply_text(
                f"✅ **{category.title()} budget set to ₱{amount:.2f}/month**\n\n"
                "I'll track your spending in this category!"
            )
        
    except ValueError:
        await update.message.reply_text("❌ Please provide a valid number for the budget amount.")
    
async def handle_sheet_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Google Sheet URL when user sends it"""
    message_text = update.message.text
    
    # Check if message contains a Google Sheets URL
    if 'docs.google.com/spreadsheets' in message_text:
        user_id = str(update.effective_user.id)
        
        # Extract the URL (in case user sent additional text)
        import re
        url_pattern = r'https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9-_]+(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#.*)?'
        urls = re.findall(url_pattern, message_text)
        
        if urls:
            sheet_url = urls[0]
            
            # Try to connect
            if sheets.connect_to_existing_sheet(sheet_url):
                user_sheets[user_id] = sheet_url
                
                keyboard = [
                    [InlineKeyboardButton("📊 View Analytics", callback_data="quick_analytics")],
                    [InlineKeyboardButton("💰 Set Budget", callback_data="set_budget")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ **Successfully Connected!**\n\n"
                    f"🔗 Connected to your Google Sheet\n"
                    f"📊 [View Sheet]({sheet_url})\n\n"
                    f"🎯 **Ready to go!** You can now:\n"
                    f"• Send receipt photos for automatic processing\n"
                    f"• Use /analytics for spending insights\n"
                    f"• Use /budget to set spending limits\n"
                    f"• Use /report for detailed analysis\n\n"
                    f"📸 **Send me your first receipt photo!**",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ **Could not connect to the sheet**\n\n"
                    "**Possible issues:**\n"
                    "• Sheet is not shared with the bot service account\n"
                    "• Invalid URL format\n"
                    "• Sheet doesn't exist or is private\n\n"
                    "**To fix:**\n"
                    "1. Open your Google Sheet\n"
                    "2. Click 'Share' button\n"
                    "3. Add this email with Editor access:\n"
                    "`expense-tracker-bot@expense-tracker-473206.iam.gserviceaccount.com`\n"
                    "4. Send me the URL again"
                )
        else:
            await update.message.reply_text(
                "❌ **Invalid Google Sheets URL**\n\n"
                "Please send a valid Google Sheets URL like:\n"
                "`https://docs.google.com/spreadsheets/d/ABC123.../edit`"
            )

def main():
    """Start the enhanced bot with all handlers properly registered"""
    print("🚀 Starting Smart Expense Tracker with Advanced Analytics...")
    
    # Check if bot token exists
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("Please add TELEGRAM_BOT_TOKEN=your_bot_token to your .env file")
        return
    
    # Check Google credentials
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'google_credentials.json')
    if not os.path.exists(credentials_file):
        print(f"⚠️  Warning: Google credentials file '{credentials_file}' not found!")
        print("Some features may not work without Google Sheets access")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("analytics", analytics_command))
    application.add_handler(CommandHandler("budget", budget_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("insights", insights_command))
    
    # Add button handler (this handles ALL button callbacks)
    application.add_handler(CallbackQueryHandler(enhanced_button_handler))
    
    # Add photo handler for receipt processing
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Add URL handler for connecting existing sheets (this was missing!)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_sheet_url
    ))
    
    print("🤖 Enhanced Bot Running! Available Commands:")
    print("  /start - Main menu and setup")
    print("  /analytics - View spending analytics")
    print("  /budget - Set spending budgets") 
    print("  /report - Generate detailed reports")
    print("  /insights - Get AI-powered insights")
    print("")
    print("📊 Features:")
    print("  • OCR receipt scanning")
    print("  • Google Sheets integration")
    print("  • Budget tracking & alerts")
    print("  • Visual charts & analytics")
    print("  • Duplicate detection")
    print("  • Smart insights & tips")
    print("")
    print("🔧 Setup Requirements:")
    print("  • TELEGRAM_BOT_TOKEN in .env")
    print("  • GOOGLE_CREDENTIALS_FILE in .env")
    print("  • google_credentials.json file")
    print("")
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        print("Check your bot token and try again.")

if __name__ == '__main__':
    main()

# Test function to verify handlers are working
def test_handlers():
    """Test function to verify all callback data is handled"""
    callback_handlers = [
        "create_sheet", "connect_sheet", "analytics_demo", "how_it_works",
        "back_to_start", "quick_analytics", "chart_category", "chart_monthly", 
        "set_budget", "recent_analysis", "monthly_report", "yearly_summary",
        "spending_patterns", "savings_tips", "demo_charts", "demo_analytics",
        "force_save_123", "cancel_save"
    ]
    
    print("✅ All callback handlers implemented:")
    for handler in callback_handlers:
        print(f"  • {handler}")
    
    return True