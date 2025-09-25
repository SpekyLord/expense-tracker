import pytesseract
import cv2
import numpy as np
from PIL import Image
import os
import re
from datetime import datetime

class ReceiptOCR:
    def __init__(self):
        # Set Tesseract path
        tesseract_path = os.getenv('TESSERACT_PATH')
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print("✅ Tesseract OCR ready!")
        else:
            print("❌ Tesseract not found. Check your installation.")
    
    def classify_category(self, text, merchant):
        """Try to guess the category based on text and merchant"""
        text_lower = (text + " " + merchant).lower()
        
        # Food & Dining
        if any(word in text_lower for word in ['restaurant', 'cafe', 'pizza', 'burger', 'food', 'dining', 'kitchen', 'grill', 'deli', 'bakery']):
            return 'Food & Dining'
        
        # Groceries
        if any(word in text_lower for word in ['grocery', 'market', 'supermarket', 'walmart', 'target', 'costco', 'kroger', 'safeway']):
            return 'Groceries'
        
        # Gas & Transportation
        if any(word in text_lower for word in ['gas', 'fuel', 'station', 'shell', 'chevron', 'exxon', 'bp', 'uber', 'lyft']):
            return 'Transportation'
        
        # Shopping
        if any(word in text_lower for word in ['store', 'shop', 'mall', 'amazon', 'clothing', 'apparel']):
            return 'Shopping'
        
        # Entertainment
        if any(word in text_lower for word in ['movie', 'theater', 'cinema', 'game', 'entertainment', 'bar', 'club']):
            return 'Entertainment'
        
        # Health & Medical
        if any(word in text_lower for word in ['pharmacy', 'cvs', 'walgreens', 'medical', 'doctor', 'hospital']):
            return 'Health & Medical'
        
        return 'General'
    
    def read_receipt(self, image_path):
        """Read text from a receipt image"""
        try:
            print(f"📖 Reading text from: {image_path}")
            
            # Load the image
            image = cv2.imread(image_path)
            
            # Convert to grayscale for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Extract text using Tesseract
            extracted_text = pytesseract.image_to_string(gray)
            
            print("✅ Text extraction complete!")
            return extracted_text
            
        except Exception as e:
            print(f"❌ Error reading receipt: {e}")
            return None
    
    def extract_info(self, text):
        """Extract useful information from receipt text"""
        if not text:
            return {"error": "No text found"}
        
        merchant = self.find_merchant(text)

        info = {
            "raw_text": text,
            "total_amount": self.find_total(text),
            "date": self.find_date(text),
            "merchant": merchant,
            "category": self.classify_category(text, merchant),
            "notes": f"Auto-extracted from receipt"
        }
        
        return info
    
    def find_total(self, text):
        """Try to find the total amount"""
        # Look for patterns like $12.34, 12.34, Total: 12.34
        patterns = [
            r'total[:\s]*\$?(\d+\.\d{2})',
            r'\$(\d+\.\d{2})',
            r'(\d+\.\d{2})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                # Return the largest amount found (likely the total)
                amounts = [float(match) for match in matches]
                return max(amounts)
        
        return None
    
    def find_date(self, text):
        """Try to find the date"""
        # Look for date patterns like 12/25/2023, 2023-12-25, Dec 25 2023
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)
        
        return "Date not found"
    
    def find_merchant(self, text):
        """Try to find the merchant/store name"""
        lines = text.split('\n')
        # Usually the merchant is in the first few lines
        for line in lines[:3]:
            line = line.strip()
            if len(line) > 3 and not re.match(r'^\d', line):
                return line
        
        return "Merchant not found"