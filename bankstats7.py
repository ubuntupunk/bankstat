import os
import pandas as pd
import tabula
from datetime import datetime
import pdfplumber
import re
from decimal import Decimal, InvalidOperation

# Function to get PDF files from a folder
def get_pdf_files(folder_path):
    return [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

# Function to parse PDF filename for dates
def parse_pdf_name(pdf_name):
    pattern = r'(\d{2}\s\w{3}\s\d{4})\s-\s(\d{2}\s\w{3}\s\d{4})\.pdf'
    match = re.match(pattern, pdf_name)
    if match:
        start_date = datetime.strptime(match.group(1), '%d %b %Y')
        end_date = datetime.strptime(match.group(2), '%d %b %Y')
        return start_date, end_date
    return None, None

# Function to extract text from all pages of a PDF
def extract_pdf_content(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages)

# Function to parse the account summary section
def parse_account_summary(content):
    summary = {}
    patterns = {
        'statement_period': r'Statement period:?\s*(.*)',
        'opening_balance': r'Opening balance:?\s*([-\d,.]+)',
        'closing_balance': r'Closing balance:?\s*([-\d,.]+)',
        'total_credits': r'Total (Funds Received|Credits):?\s*([-\d,.]+)',
        'total_debits': r'Total (Funds used|Debits):?\s*([-\d,.]+)',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            value = match.group(1) if key == 'statement_period' else match.group(2)
            value = value.replace(',', '')
            summary[key] = Decimal(value) if key != 'statement_period' else value
    return summary


# Function to parse the transaction list
def parse_transactions(content):
    transactions = []
    pattern = r'(\d{2}/\d{2}/\d{4})\s+(.*?)\s+([-\d,.]+)\s*([-\d,.]*)\s*([-\d,.]*)'
    matches = re.findall(pattern, content)
    for match in matches:
        date, description, amount1, amount2, amount3 = match
        try:
            amounts = [Decimal(a.replace(',', '')) for a in [amount1, amount2, amount3] if a]
            if len(amounts) == 1:
                transactions.append((date, description.strip(), Decimal('0'), amounts[0], Decimal('0')))
            elif len(amounts) == 2:
                transactions.append((date, description.strip(), Decimal('0'), amounts[0], amounts[1]))
            elif len(amounts) == 3:
                transactions.append((date, description.strip(), amounts[0], amounts[1], amounts[2]))
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

# Main execution function
def main():
    folder_path = input("Enter the folder path containing bank statements: ")
    pdf_files = get_pdf_files(folder_path)

    if not pdf_files:
        print("No PDF files found in the specified folder.")
        return

    print("Available PDF files:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"{i}. {pdf}")

    selection = int(input("Select a PDF file number: ")) - 1
    selected_pdf = pdf_files[selection]

    start_date, end_date = parse_pdf_name(selected_pdf)
    if start_date and end_date:
        print(f"Selected statement period: {start_date.strftime('%d %B %Y')} to {end_date.strftime('%d %B %Y')}")
    else:
        print("Unable to parse date from filename.")

    convert_option = input("Do you want to convert the PDF to CSV and analyze the data? (yes/no): ").lower()

    if convert_option == 'yes':
        pdf_path = os.path.join(folder_path, selected_pdf)
        csv_path = os.path.join(folder_path, f"{os.path.splitext(selected_pdf)[0]}.csv")

        # Read PDF and combine all tables
        dfs = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        combined_df = pd.concat(dfs, ignore_index=True)

        # Write combined data to CSV
        combined_df.to_csv(csv_path, index=False)
        print(f"PDF converted to CSV: {csv_path}")

        # Analyze the CSV data
        summary, transactions = finance_manager(pdf_path)
        print("Transactions:")
        for transaction in transactions:
            print(f"Date: {transaction[0]}, Description: {transaction[1]}, Amount: R{transaction[2]:.2f}")
    else:
        print("PDF conversion and analysis skipped.")

# Execute the main function
if __name__ == "__main__":
    main()
