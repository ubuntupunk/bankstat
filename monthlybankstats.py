import csv
from tabula import convert_into
import os
import re
from datetime import datetime

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

        # Convert PDF to CSV
        convert_into(pdf_path, csv_path, output_format="csv", pages='all')
        print(f"PDF converted to CSV: {csv_path}")

        # Analyze the CSV data
        transactions = finance_manager(csv_path)
        print("Transactions:")
        for transaction in transactions:
            print(transaction)
    else:
        print("PDF conversion and analysis skipped.")

def finance_manager(file):
    sum = 0
    transactions = []
    with open(file, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)
        for row in csv_reader:
            #get name, amount, currency
            name = row[4]
            amount = float(row[7])
            date = row[1]

            transaction = (date, name, amount)
            sum += amount
            transactions.append(transaction)
    print(f"The sum of your transactions this month is {sum}")
    print('')
    return transactions

if __name__ == "__main__":
    main()
