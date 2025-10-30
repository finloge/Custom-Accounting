__version__ = "0.0.1"

import frappe

from custom_accounting.custom_accounting.report.report_override.general_ledger import execute as custom_general_ledger

import erpnext.accounts.report.general_ledger.general_ledger

erpnext.accounts.report.general_ledger.general_ledger.execute = custom_general_ledger