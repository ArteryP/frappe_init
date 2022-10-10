import datetime
import json
import sys

import frappe
import requests
from frappe.utils.install import complete_setup_wizard
from frappe.desk.page.setup_wizard.setup_wizard import make_records


print('Setup Wizard')
complete_setup_wizard()

now = datetime.datetime.now()
year = now.year

fy = frappe.get_doc(
    {
        "doctype": "Fiscal Year",
        "year": f"{year}-{year+1}",
        "year_end_date": f"{year+1}-03-31",
        "year_start_date": f"{year}-04-01",
    }
)
try:
    fy.save()
except:
    pass


def fetch_records():
    try:
        json_file = sys.argv[1]
    except:
        json_file = '/tmp/records.json'
        json_url = 'https://raw.githubusercontent.com/ChillarAnand/frappe_init/main/records.json'
        response = requests.get(json_url)
        with open(json_file, 'w') as fh:
            fh.write(response.text)

    records = json.loads(open(json_file).read())
    return records


def create_records(records):
    for record in records:
        print(f"Processing {record['doctype']}")

        frappe.db.commit()
        try:
            if record.get('name'):
                exists = frappe.db.exists(record['doctype'], record['name'])
            else:
                _record = {}
                for key, value in record.items():
                    if not isinstance(value, str):
                        continue
                    _record[key] = value

                exists = frappe.db.exists(_record)

            if not exists:
                print(f"{record['doctype']}     Creating")
                print(record)
                make_records([record])
                frappe.db.commit()
            else:
                print(f"{record['doctype']}     Exists")
        except ImportError as e:
            frappe.db.rollback()
            print('Failed ' + record['doctype'])
            print(str(e))


records = fetch_records()
create_records(records)


# finish onboarding
modules = frappe.get_all('Module Onboarding', fields=['name'])
for module in modules:
    module_doc = frappe.get_doc('Module Onboarding', module.name)
    if not module_doc.check_completion():
        steps = module_doc.get_steps()
        for step in steps:
            step.is_complete = True
            step.save()


# set password for all users
frappe.flags.in_test = True

users = frappe.get_all('User', pluck='name')
for user in users:
    user = frappe.get_doc('User', user)
    user.new_password = 'p'
    user.save()


# settings
hr_settings = frappe.get_doc("HR Settings")
hr_settings.standard_working_hours = 2
hr_settings.save()


# holiday_list = frappe.get_doc('Holiday List', 'weekends')
# company = frappe.get_doc('Company', 'AvilPage')
# company.default_holiday_list = holiday_list.name
# company.default_currency = "INR"
# company.save()


frappe.db.commit()
