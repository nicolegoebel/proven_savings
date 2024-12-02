import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

class SavingsTracker:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.transactions_file = self.data_dir / "transactions.csv"
        self._initialize_data()

    def _initialize_data(self):
        """Initialize the transactions file if it doesn't exist."""
        if not self.transactions_file.exists():
            df = pd.DataFrame(columns=[
                'date', 'amount', 'category', 'description'
            ])
            df.to_csv(self.transactions_file, index=False)

    def add_transaction(self, amount: float, category: str, description: str = ""):
        """Add a new savings transaction."""
        new_transaction = pd.DataFrame([{
            'date': datetime.now().strftime('%Y-%m-%d'),
            'amount': amount,
            'category': category,
            'description': description
        }])
        
        df = pd.read_csv(self.transactions_file)
        df = pd.concat([df, new_transaction], ignore_index=True)
        df.to_csv(self.transactions_file, index=False)

    def get_total_savings(self) -> float:
        """Calculate total savings."""
        df = pd.read_csv(self.transactions_file)
        return df['amount'].sum()

    def get_savings_by_category(self) -> pd.Series:
        """Get savings grouped by category."""
        df = pd.read_csv(self.transactions_file)
        return df.groupby('category')['amount'].sum()

def main():
    tracker = SavingsTracker()
    print("Welcome to Proven Savings!")
    print(f"Total savings: ${tracker.get_total_savings():,.2f}")

if __name__ == "__main__":
    main()
