"""
Status tracking for the lead generation system
"""
import json
from datetime import datetime
import os

class StatusTracker:
    """Track system status and write to status.txt"""
    
    def __init__(self, status_file='data/status.txt'):
        self.status_file = status_file
        self.stats = {
            'last_run': None,
            'businesses_scraped': 0,
            'websites_checked': 0,
            'leads_in_sheet': 0,
            'errors': 0,
            'next_run': None
        }
        self.load()
    
    def load(self):
        """Load existing status if available"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r') as f:
                    content = f.read()
                    # Parse simple key: value format
                    for line in content.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip().lower().replace(' ', '_')
                            value = value.strip()
                            if key in self.stats:
                                # Try to convert to int if possible
                                try:
                                    self.stats[key] = int(value)
                                except:
                                    self.stats[key] = value
            except Exception as e:
                print(f"Could not load status: {e}")
    
    def update(self, **kwargs):
        """Update stats"""
        self.stats.update(kwargs)
        self.stats['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def save(self):
        """Save status to file"""
        os.makedirs('data', exist_ok=True)
        with open(self.status_file, 'w') as f:
            f.write(f"Last Run: {self.stats['last_run']}\n")
            f.write(f"Businesses Scraped: {self.stats['businesses_scraped']}\n")
            f.write(f"Websites Checked: {self.stats['websites_checked']}\n")
            f.write(f"Leads in Sheet: {self.stats['leads_in_sheet']}\n")
            f.write(f"Errors: {self.stats['errors']}\n")
            f.write(f"Next Run: {self.stats['next_run']}\n")
    
    def increment(self, key, amount=1):
        """Increment a counter"""
        if key in self.stats:
            self.stats[key] += amount
