import pdfplumber
import re
from decimal import Decimal, InvalidOperation

# Function to extract text from all pages of a PDF
def extract_pdf_content(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages)

# Function to parse the account summary section
def parse_account_summary(content):
    summary = {}
    patterns = {
        'statement_period': r'Statement period:\s*(.*)',
        'opening_balance': r'Opening balance\s*([-\d,.]+)',
        'closing_balance': r'Closing balance\s*([-\d,.]+)',
        'total_credits': r'Total Funds Received/credits\s*([-\d,.]+)',
        'total_debits': r'Total Funds used/debits\s*([-\d,.]+)',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            value = match.group(1).replace(',', '')
            summary[key] = Decimal(value) if key != 'statement_period' else value
    return summary

# Function to parse the transaction list
def parse_transactions(content):
    transactions = []
    pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([-\d,.]+)\s+([-\d,.]+)\s+([-\d,.]+)'
    matches = re.findall(pattern, content)
    for match in matches:
        date, description, fees, debits, credits = match
        try:
            fees = Decimal(fees.replace(',', '')) if fees else Decimal('0')
            debits = Decimal(debits.replace(',', '')) if debits else Decimal('0')
            credits = Decimal(credits.replace(',', '')) if credits else Decimal('0')
            transactions.append((date, description.strip(), fees, debits, credits))
        except InvalidOperation:
            print(f"Warning: Invalid amount format for transaction on {date}")
    return transactions

# Main function to manage the finance data
def finance_manager(pdf_path):
    # Extract content from PDF
    content = extract_pdf_content(pdf_path)
    
    # Parse account summary and transactions
    summary = parse_account_summary(content)
    transactions = parse_transactions(content)

    # Validate extracted data
    if 'opening_balance' not in summary or 'closing_balance' not in summary:
        print("Warning: Opening or closing balance not found in the statement.")
    
    # Calculate and validate totals
    calculated_total_debits = sum(t[3] for t in transactions)
    calculated_total_credits = sum(t[4] for t in transactions)
    if 'total_debits' in summary and abs(calculated_total_debits - summary['total_debits']) > Decimal('0.01'):
        print(f"Warning: Calculated total debits ({calculated_total_debits}) doesn't match statement ({summary['total_debits']})")
    if 'total_credits' in summary and abs(calculated_total_credits - summary['total_credits']) > Decimal('0.01'):
        print(f"Warning: Calculated total credits ({calculated_total_credits}) doesn't match statement ({summary['total_credits']})")

    # Print summary and transactions
    print("Account Summary:")
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("\nTransactions:")
    for transaction in transactions:
        print(f"Date: {transaction[0]}, Description: {transaction[1]}, Fees: R{transaction[2]:.2f}, Debits: R{transaction[3]:.2f}, Credits: R{transaction[4]:.2f}")

    return summary, transactions

# Main execution
pdf_path = "path_to_your_pdf_file.pdf"
summary, transactions = finance_manager(pdf_path)
