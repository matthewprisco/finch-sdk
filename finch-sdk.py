import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from finch import Finch
from finch._utils import parse_date
from datetime import datetime, timedelta


# Finch API credentials
FINCH_API_BASE_URL = "https://api.tryfinch.com"  # Update if needed
ACCESS_TOKEN = "39194c81-3799-4359-836f-37036ec0e8b3"  # Replace with actual Finch API token
# ACCESS_TOKEN = "b07542b9-4d9f-4da8-b793-9d66e2ca72de"  # Replace with actual Finch API token

# Google Sheets credentials
GOOGLE_SHEET_ID = "1_Yj-DeRDvyNAz0WoiGwFeUsw9daD1-5GDcmTe7pnrTE"  # Replace with your Google Sheet ID
BENADMIN_SHEET_NAME = "BenAdmin Master"  # Sheet name for employee data
PAYROLL_SHEET_NAME = "PayRoll Master"  # Sheet name for payroll data

# Finch API Client
client = Finch(access_token=ACCESS_TOKEN)

def authenticate_google_sheets():
    """Authenticate and return Google Sheets client."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google-sdk.json", scope)
    client = gspread.authorize(creds)
    return client

def filter_list(list, type):
    """Extracts email of a given type (work or personal) from the emails list."""
    for item in list:
        if item.type == type:
            return item.data
    return "N/A"

def write_to_benadmin_master(sheet, employees, metrics):
    """Writes employee directory data to the BenAdmin Master Google Sheet."""
    sheet.clear()  # Clear old data
    headers = [
        "Employee ID", "First Name", "Middle Name",  "Last Name", "SSN", "Birth Date", "Status", "Hire Date", "Termination Date", "Employment Type",
        # "Personal Email", "Work Email", "Personal Phone", "Work Phone",
         "City", "State", "Country", "Postal Code", "ATNE (12 Months)", "ATNE (Prior Year)", "COBRA Eligible", "ERISA Start", "ERISA End", "ACA FTE"
    ]
    sheet.append_row(headers)  # Add headers

    employee_data = [
        [
            emp_id,
            emp["first_name"],
            emp["middle_name"],
            emp["last_name"],
            emp["ssn"],
            emp["dob"],
            emp["employment_status"],
            emp["hire_date"],
            emp["termination_date"],
            emp["employment_type"],
            # emp["personal_email"],
            # emp["work_email"],
            # emp["personal_phone"],
            # emp["work_phone"],
            emp["city"],
            emp["state"],
            emp["country"],
            emp["postal_code"],
            metrics["atne_12_months"],
            metrics["atne_prior_year"],
            metrics["cobra_eligible"],
            metrics["erisa_start"],
            metrics["erisa_end"],
            metrics["aca_fte"],

        ]
        for emp_id, emp in employees.items()
    ]

    sheet.append_rows(employee_data)  # Append new data
    print(f"Employee data successfully written to {BENADMIN_SHEET_NAME}!")

def write_to_payroll_master(sheet, payroll_data):
    """Writes payroll-related data (pay statements & payment responses) to the Payroll Master Google Sheet."""
    # sheet.clear()  # Clear old data
    # headers = [
    #     "Employee ID", "Month", "File Date", "Benefit Line", "First Name", "Last Name",
    #     "DOB (PD)", "Deduction (PD)", "Frequency", '={"Deduction (Monthly)"; arrayformula(if(H2:H="",,ifs(I2:I="weekly",H2:H*52/12, I2:I="bi_weekly",H2:H*26/12, I2:I="semi_monthly",H2:H*2, I2:I="monthly",H2:H, I2:I="annually",H2:H/12)))}',
    #     # "Personal Phone", "Work Phone", "City", "State", "Country", "Postal Code",
    #     # "Pay Start Date", "Pay End Date", "Pay Frequency"
    # ]
    # sheet.append_row(headers)  # Add headers
   # Get existing data
    num_rows = len(sheet.get_all_values())
    # Clear only data below the first row
    if num_rows > 1:
        sheet.batch_clear([f"A2:Z{num_rows}"])  # Adjust range based on your sheet
        # Append new data starting from the second row
    sheet.append_rows(payroll_data)

    print(f"Payroll data successfully written to {PAYROLL_SHEET_NAME}!")

def fetch_payroll_data():
    """Fetch payroll data from Finch API and store in Google Sheets."""
    google_client = authenticate_google_sheets()
    benadmin_sheet = google_client.open_by_key(GOOGLE_SHEET_ID).worksheet(BENADMIN_SHEET_NAME)
    payroll_sheet = google_client.open_by_key(GOOGLE_SHEET_ID).worksheet(PAYROLL_SHEET_NAME)

    directory = client.hris.directory.list()
    individuals = {"responses": []}
    try:
        for emp in directory.individuals:
            try:
                page = client.hris.individuals.retrieve_many(
                    requests=[{"individual_id": emp.id}],
                    options={
                        "include": ["ssn"]
                    }
                )
                
                individuals["responses"].append(page.responses[0])
            except Exception as e:
                print("Finch API Error:", e)

    except Exception as e:
        print("Failed to retrieve individuals directory:", e)


    employements = {}
    try:
        for emp in directory.individuals:
            try:
                page = client.hris.employments.retrieve_many(
                    requests=[{"individual_id": emp.id}]
                )
                employements.update({
                    emp.body.id: {
                        "first_name": emp.body.first_name,
                        "last_name": emp.body.last_name,
                        "title": emp.body.title,
                        "is_active": emp.body.is_active,
                        "employment_status": emp.body.employment_status,
                        # "employment_status": "Active" if emp.body.employment_status == 'active' else "Terminated",
                        "start_date": emp.body.start_date,
                        "end_date": emp.body.latest_rehire_date,
                        "employment_type": emp.body.employment.subtype
                    }
                    for emp in page.responses
                })
            except Exception as e:
                print("Finch API Error:", e)

    except Exception as e:
        print("Failed to retrieve individuals directory:", e)
        
    employees = {
        emp.body.id: {
            "first_name": emp.body.first_name,
            "middle_name": emp.body.middle_name,
            "last_name": emp.body.last_name,
            "personal_email": filter_list(emp.body.emails, "personal"),
            "work_email": filter_list(emp.body.emails, "work"),
            "personal_phone": filter_list(emp.body.phone_numbers, "personal"),
            "work_phone": filter_list(emp.body.phone_numbers, "work"),
            
            "city": emp.body.residence.city,
            "state": emp.body.residence.state,
            "country": emp.body.residence.country,
            "postal_code": emp.body.residence.postal_code,
            "dob": emp.body.dob,
            "employment_type": employements[emp.body.id]['employment_type'],
            "is_active": employements[emp.body.id]['is_active'],
            "employment_status": employements[emp.body.id]["employment_status"]
                if employements[emp.body.id]["employment_status"] is not None
                else ("Active" if employements[emp.body.id]["is_active"] == 1 else "Terminated"),
            "hire_date": employements[emp.body.id]["start_date"],
            "termination_date": employements[emp.body.id]["end_date"],
            "ssn": emp.body.ssn,
        }
        for emp in individuals["responses"]
    }

    metrics = calculate_metrics(employees)
    # Write employee directory data to BenAdmin Master
    write_to_benadmin_master(benadmin_sheet, employees, metrics)

    # Fetch Payroll Payments
    start_date = "2023-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    payments = client.hris.payments.list(
        end_date=parse_date(end_date),
        start_date=parse_date(start_date),
    )

    if not payments.items:
        print("No payments found for the given date range.")
        return

    payment_data = {
        p.id: {
            "pay_date": p.pay_date,
            "gross_pay": p.gross_pay.amount,
            "net_pay": p.net_pay.amount,
            "frequency": p.pay_frequencies[0] if p.pay_frequencies and isinstance(p.pay_frequencies, list) else "monthly",
            "start_date": p.pay_period.start_date,
            "end_date": p.pay_period.end_date,
        }
        for p in payments.items
    }
    
    pay_statements_request = [{"payment_id": str(p.id)} for p in payments.items if p.id]

    try:
        pay_statements_response = client.hris.pay_statements.retrieve_many(requests=pay_statements_request)
        pay_statements = pay_statements_response.responses if hasattr(pay_statements_response, "responses") else []
    except Exception as e:
        print(f"Error fetching pay statements: {e}")
        return
#  "Employee ID", "Month", "File Date", "Benefit Line", "First Name", "Last Name",
#         "DOB (PD)", "Deduction (PD)", "Frequency", "Deduction (Monthly)",
    payroll_data = []
    for statement in pay_statements:
        payment_id = statement.payment_id
        for emp in statement.body.pay_statements:
            emp_id = emp.individual_id
            deductionAmount = 0
            # deductionAmount = emp.employee_deductions[0].amount if emp.employee_deductions and isinstance(emp.employee_deductions, list) else 0,
            contributionAmount = 0
            date_obj = datetime.strptime(payment_data[payment_id]["pay_date"], "%Y-%m-%d")
            for deduction in emp.employee_deductions:
                benefitName = deduction.name
                deductionAmount += deduction.amount
            # benefitName = emp.employee_deductions[0].name if emp.employee_deductions and isinstance(emp.employee_deductions, list) else "",
            # benefitName = "401k"
            for contribution in emp.employer_contributions:
                contributionAmount += contribution.amount
                

            # Given pay period
            start_date = datetime.strptime(payment_data[payment_id]["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(payment_data[payment_id]["end_date"], "%Y-%m-%d")

            # Calculate the number of days in the pay period
            pay_period_days = (end_date - start_date).days

            # Determine pay frequency
            if pay_period_days == 1:
                frequency = "daily"
            elif pay_period_days == 7:
                frequency = "weekly"
            elif pay_period_days == 14:
                frequency = "bi_weekly"
            elif pay_period_days in [15, 16]:
                frequency = "semi_monthly"
            elif pay_period_days in [30, 31]:
                frequency = "monthly"
            elif pay_period_days >= 180:
                frequency = "Semi-annual"
            elif pay_period_days >= 365:
                frequency = "annually"
            else:
                frequency = "Unknown"

            # monthly_deduction = 0
            # if frequency == "weekly":
            #     monthly_deduction = deductionAmount * 52 / 12
            # elif frequency == "bi_weekly":
            #     monthly_deduction = deductionAmount * 26 / 12
            # elif frequency == "semi_monthly":
            #     monthly_deduction = deductionAmount * 2
            # elif frequency == "monthly":
            #     monthly_deduction = deductionAmount
            # elif frequency == "annually":
            #     monthly_deduction = deductionAmount / 12
            # else:
            #     monthly_deduction = 0  # Handle unexpected values
            
            payroll_data.append([
                emp_id,
                date_obj.strftime("%m"),
                payment_data[payment_id]["pay_date"],
                benefitName,
                employees[emp_id]["first_name"],
                employees[emp_id]["last_name"],
                employees[emp_id]["dob"],
                deductionAmount,
                frequency,
                # monthly_deduction
            ])
    # Write payroll data to Payroll Master
    write_to_payroll_master(payroll_sheet, payroll_data)
def calculate_metrics(employees):
    """Calculate compliance metrics based on employee data."""
    def calculate_atne(employees, period):
        now = datetime.now()
        if period == '12_months':
            end_date = now.replace(day=1)
            start_date = (end_date - timedelta(days=365)).replace(day=1)
            months = []
            current = start_date
            for _ in range(12):
                months.append(current)
                current = (current + timedelta(days=32)).replace(day=1)
        elif period == 'prior_year':
            prior_year = now.year - 1
            months = [datetime(prior_year, m, 1) for m in range(1, 13)]
        else:
            return 0.0

        total = 0
        for month in months:
            if month.month == 12:
                month_end = month.replace(year=month.year+1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month.replace(month=month.month+1, day=1) - timedelta(days=1)
            
            month_count = 0
            for emp in employees.values():
                try:
                    hire_date = datetime.strptime(emp['hire_date'], "%Y-%m-%d") if emp['hire_date'] else None
                    term_date = datetime.strptime(emp['termination_date'], "%Y-%m-%d") if emp['termination_date'] else None
                except:
                    continue
                
                active = False
                if hire_date and hire_date <= month_end:
                    if not term_date or term_date >= month.replace(day=1):
                        active = True
                if active:
                    month_count += 1
            total += month_count
        return round(total / len(months), 2) if len(months) > 0 else 0.0

    def is_cobra_eligible(employees):
        prior_year = datetime.now().year - 1
        eligible_days = 0
        
        for month in range(1, 13):
            month_start = datetime(prior_year, month, 1)
            if month == 12:
                month_end = datetime(prior_year, 12, 31)
            else:
                month_end = datetime(prior_year, month+1, 1) - timedelta(days=1)
            
            active_count = 0
            for emp in employees.values():
                try:
                    hire_date = datetime.strptime(emp['hire_date'], "%Y-%m-%d") if emp['hire_date'] else None
                    term_date = datetime.strptime(emp['termination_date'], "%Y-%m-%d") if emp['termination_date'] else None
                except:
                    continue
                
                if hire_date and hire_date <= month_end:
                    if not term_date or term_date >= month_start:
                        active_count += 1
            
            if active_count >= 20:
                eligible_days += (month_end - month_start).days + 1
        
        return eligible_days >= 183

    def erisa_counts(employees):
        prior_year = datetime.now().year - 1
        start_date = datetime(prior_year, 1, 1)
        end_date = datetime(prior_year, 12, 31)
        start_count = 0
        end_count = 0
        
        for emp in employees.values():
            try:
                hire_date = datetime.strptime(emp['hire_date'], "%Y-%m-%d") if emp['hire_date'] else None
                term_date = datetime.strptime(emp['termination_date'], "%Y-%m-%d") if emp['termination_date'] else None
            except:
                continue
            
            if hire_date and hire_date <= start_date:
                if not term_date or term_date >= start_date:
                    start_count += 1
            
            if hire_date and hire_date <= end_date:
                if not term_date or term_date >= end_date:
                    end_count += 1
        
        return start_count, end_count

    def aca_fte(employees):
        prior_year = datetime.now().year - 1
        total_fte = 0.0
        
        for month in range(1, 13):
            month_start = datetime(prior_year, month, 1)
            if month == 12:
                month_end = datetime(prior_year, 12, 31)
            else:
                month_end = datetime(prior_year, month+1, 1) - timedelta(days=1)
            
            monthly_ft = 0
            monthly_pt_hours = 0
            
            for emp in employees.values():
                try:
                    hire_date = datetime.strptime(emp['hire_date'], "%Y-%m-%d") if emp['hire_date'] else None
                    term_date = datetime.strptime(emp['termination_date'], "%Y-%m-%d") if emp['termination_date'] else None
                except:
                    continue
                
                if hire_date and hire_date <= month_end and (not term_date or term_date >= month_start):
                    emp_type = emp.get('employment_type', '').lower()
                    if emp_type == 'full_time':
                        monthly_ft += 1
                    else:
                        # Assume part-time employees work 15 hours/week = 60 hours/month
                        monthly_pt_hours += 60
            
            monthly_fte = monthly_ft + (monthly_pt_hours / 120)
            total_fte += monthly_fte
        
        return round(total_fte / 12, 2)

    return {
        'atne_12_months': calculate_atne(employees, '12_months'),
        'atne_prior_year': calculate_atne(employees, 'prior_year'),
        'cobra_eligible': is_cobra_eligible(employees),
        'erisa_start': erisa_counts(employees)[0],
        'erisa_end': erisa_counts(employees)[1],
        'aca_fte': aca_fte(employees)
    }

# Run the function
fetch_payroll_data()


