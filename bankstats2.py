import csv
import tabula
import os
import re
from datetime import datetime
import pandas as pd
from decimal import Decimal

def get_pdf_files(folder_path):
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    return pdf_files

def parse_pdf_name(pdf_name):
    pattern = r'(\d{2}\s\w{3}\s\d{4})\s-\s(\d{2}\s\w{3}\s\d{4})\.pdf'
    match = re.match(pattern, pdf_name)
    if match:
        start_date = datetime.strptime(match.group(1), '%d %b %Y')
        end_date = datetime.strptime(match.group(2), '%d %b %Y')
        return start_date, end_date
    return None, None

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
        transactions = finance_manager(csv_path)
        print("Transactions:")
        for transaction in transactions:
            print(transaction)
    else:
        print("PDF conversion and analysis skipped.")
        
    transactions = finance_manager(csv_path)
    print("Transactions:")
    for transaction in transactions:
      print(f"Date: {transaction[0]}, Description: {transaction[1]}, Amount: R{transaction[2]:.2f}")

def finance_manager(file):
    sum_debits = Decimal('0')
    sum_credits = Decimal('0')
    transactions = []
    
    with open(file, mode='r') as csv_file:
        content = csv_file.read()
        
        # Find the line with the correct headers
        header_match = re.search(r'Date,Description,.*Debits \(R\),Credits \(R\),Balance \(R\)', content)
        if header_match:
            csv_content = content[header_match.start():]
            csv_reader = csv.reader(csv_content.splitlines())
            next(csv_reader)  # Skip the header row
            
            for row in csv_reader:
                if len(row) >= 5:
                    date = row[0]
                    description = row[1]
                    debit = Decimal(row[2].replace(',', '') or '0')
                    credit = Decimal(row[3].replace(',', '') or '0')
                    
                    sum_debits += debit
                    sum_credits += credit
                    
                    transaction = (date, description, -debit if debit else credit)
                    transactions.append(transaction)
    
    net_change = sum_credits - sum_debits
    print(f"Total debits: R{sum_debits:.2f}")
    print(f"Total credits: R{sum_credits:.2f}")
    print(f"Net change in balance: R{net_change:.2f}")
    print('')
    return transactions


if __name__ == "__main__":
    main()