Finch Payroll Integration Scripts
This script automates the retrieval of employee and payroll data from the Finch API and writes it into a Google Sheet for benefits administration and payroll tracking.

Files Overview
1. fetch_payroll_data.py
Purpose: Automates payroll data extraction from Finch and stores it in a structured Google Sheet format for benefits compliance and tracking.

Functionality:

Authenticates to Google Sheets using service credentials

Connects to the Finch API to fetch:

Employee directory data

Employment status

Payroll pay statements

Payment records

Calculates ACA/ERISA/ATNE compliance metrics

Writes employee data to BenAdmin Master

Writes payroll deductions to PayRoll Master

Key Features:

HRIS + Payroll data ingestion from Finch

Compliance metric calculations

Google Sheets integration for live data tracking

Deduction amount breakdowns by employee and frequency

Configuration
Finch API
Base URL: https://api.tryfinch.com
Access Token:
ACCESS_TOKEN = "39194c81-3799-4359-836f-37036ec0e8b3"
(Replace with secure environment variable in production)

Google Sheets
Sheet ID: 1_Yj-DeRDvyNAz0WoiGwFeUsw9daD1-5GDcmTe7pnrTE

BenAdmin Sheet Name: BenAdmin Master

Payroll Sheet Name: PayRoll Master

Credential File: google-sdk.json (Google Service Account)

Airtable (Not used in this script, but relevant for token handling elsewhere)
Dependencies
Install required packages:

bash
Copy
Edit
pip install gspread oauth2client requests finch
Ensure google-sdk.json is present and properly configured for your service account.

Usage
Run the script:

bash
Copy
Edit
python fetch_payroll_data.py
This will:

Authenticate with Google Sheets

Pull employee directory and employment data from Finch

Calculate:

ATNE (12-month and prior year averages)

COBRA eligibility

ERISA counts

ACA FTEs

Populate two Google Sheets:

BenAdmin Master

PayRoll Master

Expected Output
Console will display:

css
Copy
Edit
Employee data successfully written to BenAdmin Master!
Payroll data successfully written to PayRoll Master!
Output Fields
BenAdmin Master
Field	Description
Employee ID	Unique identifier from Finch
First/Last Name	Employee name
SSN	Social Security Number
Birth Date	Date of birth
Hire/Termination Date	Dates of employment
Employment Type	Full-time / Part-time
Address Info	City, State, Country, Postal
Compliance Metrics	ATNE, ERISA, ACA FTEs

PayRoll Master
Field	Description
Employee ID	From pay statements
Month	Derived from pay date
File Date	Payment Date
Benefit Line	Deduction category
Deduction	Total deduction amount
Frequency	Daily/Weekly/Bi-Weekly/etc.

Error Handling
Handles exceptions and logs:

Finch API connectivity issues

Google Sheets authentication or access issues

Incomplete data (missing emails, phone, SSN, etc.)

Missing employment details

Logging
Minimal logging to console:

API success/failure

Sheet update confirmation

Error traces on exception blocks

Security Notes
⚠️ Important: This script currently stores Finch API credentials in plain text.

Recommended changes:

Environment Variables:

python
Copy
Edit
import os
ACCESS_TOKEN = os.getenv("FINCH_ACCESS_TOKEN")
.env File + python-dotenv

Avoid committing google-sdk.json to Git

Next Steps
Improvements
Add a CLI or config UI

Store last sync timestamps

Add Slack/Email notifications on sync

Use a scheduler like cron, APScheduler, or PythonAnywhere task

Modularization
Break into reusable modules:

fetch_employees.py

calculate_metrics.py

update_sheets.py

Testing
Add mock testing for:

Finch API responses

Google Sheets writes

Troubleshooting
Issue	Resolution
Invalid credentials	Check Finch access token and JSON key file
Empty rows in sheet	Ensure Finch returns complete employee/employment data
Date parsing errors	Ensure all dates are in ISO format
Deduction is 0	Check if employee had active benefits during the period

API Documentation
Finch API Docs

gspread Docs

Google Sheets API

