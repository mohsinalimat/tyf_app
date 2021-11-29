import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
import frappe
from frappe.utils import flt
from frappe import _

class TYFPayrollEntry(PayrollEntry):

    def get_salary_components(self, component_type):
        salary_slips = self.get_sal_slip_list(ss_status=1, as_dict=True)
        if salary_slips:
            salary_components = frappe.db.sql("""
				select ssd.salary_component, ssd.amount, ssd.parentfield, ss.payroll_cost_center, ss.employee
				from `tabSalary Slip` ss, `tabSalary Detail` ssd
				where ss.name = ssd.parent and ssd.parentfield = '%s' and ss.name in (%s)
			""" % (component_type, ', '.join(['%s']*len(salary_slips))),
                tuple([d.name for d in salary_slips]), as_dict=True)
            return salary_components

    def get_salary_component_total(self, component_type=None):
        salary_components = self.get_salary_components(component_type)
        if salary_components:
            component_dict = {}
            for item in salary_components:
                add_component_to_accrual_jv_entry = True
                if component_type == "earnings":
                    is_flexible_benefit, only_tax_impact = frappe.db.get_value(
                        "Salary Component", item['salary_component'], ['is_flexible_benefit', 'only_tax_impact'])
                    if is_flexible_benefit == 1 and only_tax_impact == 1:
                        add_component_to_accrual_jv_entry = False
                if add_component_to_accrual_jv_entry:
                    component_dict[(item.salary_component, item.payroll_cost_center, item.employee)] \
                        = component_dict.get((item.salary_component, item.payroll_cost_center, item.employee), 0) + flt(item.amount)
            account_details = self.get_account(component_dict=component_dict)
            return account_details

    def get_account(self, component_dict=None):
        account_dict = {}
        for key, amount in component_dict.items():
            account = self.get_salary_component_account(key[0])
            account_dict[(account, key[1], key[2])] = account_dict.get(
                (account, key[1], key[2]), 0) + amount
        return account_dict

    def make_accrual_jv_entry(self):
        self.check_permission("write")
        earnings = self.get_salary_component_total(
            component_type="earnings") or {}
        deductions = self.get_salary_component_total(
            component_type="deductions") or {}
        payroll_payable_account = self.payroll_payable_account
        jv_name = ""
        precision = frappe.get_precision(
            "Journal Entry Account", "debit_in_account_currency")

        if earnings or deductions:
            journal_entry = frappe.new_doc("Journal Entry")
            journal_entry.voucher_type = "Journal Entry"
            journal_entry.user_remark = _("Accrual Journal Entry for salaries from {0} to {1}")\
                .format(self.start_date, self.end_date)
            journal_entry.company = self.company
            journal_entry.posting_date = self.posting_date
            accounting_dimensions = get_accounting_dimensions() or []

            accounts = []
            currencies = []
            payable_amount = 0
            multi_currency = 0
            company_currency = erpnext.get_company_currency(self.company)
            employee = ""

            # Earnings
            for acc_cc, amount in earnings.items():
                exchange_rate, amt = self.get_amount_and_exchange_rate_for_journal_entry(
                    acc_cc[0], amount, company_currency, currencies)
                payable_amount += flt(amount, precision)
                account_type = frappe.db.get_value(
                    "Account", acc_cc[0], "account_type")
                if account_type in ["Receivable", "Payable"]:
                    row = {
                        "account": acc_cc[0],
                        "debit_in_account_currency": flt(amt, precision),
                        "exchange_rate": flt(exchange_rate),
                        "cost_center": acc_cc[1] or self.cost_center,
                        "project": self.project,
                        "party_type": "Employee",
                        "party": acc_cc[2]
                    }
                    employee = acc_cc[2]
                else:
                    row = {
                        "account": acc_cc[0],
                        "debit_in_account_currency": flt(amt, precision),
                        "exchange_rate": flt(exchange_rate),
                        "cost_center": acc_cc[1] or self.cost_center,
                        "project": self.project
                    }

                accounts.append(self.update_accounting_dimensions(
                    row, accounting_dimensions))

            # Deductions
            for acc_cc, amount in deductions.items():
                exchange_rate, amt = self.get_amount_and_exchange_rate_for_journal_entry(
                    acc_cc[0], amount, company_currency, currencies)
                payable_amount -= flt(amount, precision)
                account_type = frappe.db.get_value(
                    "Account", acc_cc[0], "account_type")
                if account_type in ["Receivable", "Payable"]:
                    row = {
                        "account": acc_cc[0],
                        "credit_in_account_currency": flt(amt, precision),
                        "exchange_rate": flt(exchange_rate),
                        "cost_center": acc_cc[1] or self.cost_center,
                        "project": self.project,
                        "party_type": "Employee",
                        "party": acc_cc[2]
                    }
                    employee = acc_cc[2]
                else:
                    row = {
                        "account": acc_cc[0],
                        "credit_in_account_currency": flt(amt, precision),
                        "exchange_rate": flt(exchange_rate),
                        "cost_center": acc_cc[1] or self.cost_center,
                        "project": self.project
                    }

                accounts.append(self.update_accounting_dimensions(
                    row, accounting_dimensions))

            # Payable amount
            exchange_rate, payable_amt = self.get_amount_and_exchange_rate_for_journal_entry(
                payroll_payable_account, payable_amount, company_currency, currencies)
            account_type = frappe.db.get_value(
                "Account", payroll_payable_account, "account_type")
            if account_type in ["Receivable", "Payable"]:
                row = {
                    "account": payroll_payable_account,
                    "credit_in_account_currency": flt(payable_amt, precision),
                    "exchange_rate": flt(exchange_rate),
                    "cost_center": self.cost_center,
                    "party_type": "Employee",
                    "party": employee
                }
                employee = ""
            else:
                row = {
                    "account": payroll_payable_account,
                    "credit_in_account_currency": flt(payable_amt, precision),
                    "exchange_rate": flt(exchange_rate),
                    "cost_center": self.cost_center
                }

            accounts.append(self.update_accounting_dimensions(
                row, accounting_dimensions))

            journal_entry.set("accounts", accounts)
            if len(currencies) > 1:
                multi_currency = 1
            journal_entry.multi_currency = multi_currency
            journal_entry.title = payroll_payable_account
            journal_entry.save()

            try:
                journal_entry.submit()
                jv_name = journal_entry.name
                self.update_salary_slip_status(jv_name=jv_name)
            except Exception as e:
                if type(e) in (str, list, tuple):
                    frappe.msgprint(e)
                raise

        return jv_name
