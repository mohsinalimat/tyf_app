import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
from frappe.model.document import Document
from frappe.model.naming import _get_amended_name,  set_naming_from_document_naming_rule, make_autoname, set_name_from_naming_options, validate_name
import frappe
from frappe.utils import flt
from frappe import _


class TYFPayrollEntry(PayrollEntry):

    def get_salary_components(self, component_type):
        salary_slips = self.get_sal_slip_list(ss_status=1, as_dict=True)
        if salary_slips:
            salary_components = frappe.db.sql("""
				select ssd.salary_component, ssd.amount, ssd.parentfield, ss.payroll_cost_center, ss.employee, ss.budget_line
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
                    component_dict[(item.salary_component, item.payroll_cost_center, item.employee, item.budget_line)] \
                        = component_dict.get((item.salary_component, item.payroll_cost_center, item.employee), 0) + flt(item.amount)
            account_details = self.get_account(component_dict=component_dict)
            return account_details

    def get_account(self, component_dict=None):
        account_dict = {}
        for key, amount in component_dict.items():
            account = self.get_salary_component_account(key[0])
            account_dict[(account, key[1], key[2], key[3])] = account_dict.get(
                (account, key[1], key[2], key[3]), 0) + amount
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
                        "project": self.project,
                        "budget_line": acc_cc[3]
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

    @frappe.whitelist()
    def make_payment_entry(self):
        self.check_permission('write')

        salary_slip_name_list = frappe.db.sql(""" select t1.name from `tabSalary Slip` t1
        where t1.docstatus = 1 and start_date >= %s and end_date <= %s and t1.payroll_entry = %s
        """, (self.start_date, self.end_date, self.name), as_list=True)

        if salary_slip_name_list and len(salary_slip_name_list) > 0:

            for salary_slip_name in salary_slip_name_list:
                salary_slip_total = 0
                salary_slip = frappe.get_doc(
                    "Salary Slip", salary_slip_name[0])
                party = salary_slip.employee
                for sal_detail in salary_slip.earnings:
                    is_flexible_benefit, only_tax_impact, creat_separate_je, statistical_component = frappe.db.get_value("Salary Component", sal_detail.salary_component,
                                                                                                                         ['is_flexible_benefit', 'only_tax_impact', 'create_separate_payment_entry_against_benefit_claim', 'statistical_component'])
                    if only_tax_impact != 1 and statistical_component != 1:
                        if is_flexible_benefit == 1 and creat_separate_je == 1:
                            self.create_journal_entry(
                                sal_detail.amount, sal_detail.salary_component, party)
                        else:
                            salary_slip_total += sal_detail.amount
                for sal_detail in salary_slip.deductions:
                    statistical_component = frappe.db.get_value(
                        "Salary Component", sal_detail.salary_component, 'statistical_component')
                    if statistical_component != 1:
                        salary_slip_total -= sal_detail.amount
                if salary_slip_total > 0:
                    self.create_journal_entry(
                        salary_slip_total, "salary", party)

    def create_journal_entry(self, je_payment_amount, user_remark, party):
        payroll_payable_account = self.payroll_payable_account
        precision = frappe.get_precision(
            "Journal Entry Account", "debit_in_account_currency")

        accounts = []
        row = []
        currencies = []
        multi_currency = 0
        company_currency = erpnext.get_company_currency(self.company)

        exchange_rate, amount = self.get_amount_and_exchange_rate_for_journal_entry(
            self.payment_account, je_payment_amount, company_currency, currencies)
        account_type = frappe.db.get_value(
            "Account", self.payment_account, "account_type")
        if account_type in ["Receivable", "Payable"]:
            row = {
                "account": self.payment_account,
                "bank_account": self.bank_account,
                "credit_in_account_currency": flt(amount, precision),
                "exchange_rate": flt(exchange_rate),
                "party_type": "Employee",
                "party": party
            }
        else:
            row = {
                "account": self.payment_account,
                "bank_account": self.bank_account,
                "credit_in_account_currency": flt(amount, precision),
                "exchange_rate": flt(exchange_rate),
            }
        accounts.append(row)

        exchange_rate, amount = self.get_amount_and_exchange_rate_for_journal_entry(
            payroll_payable_account, je_payment_amount, company_currency, currencies)
        account_type = frappe.db.get_value(
            "Account", payroll_payable_account, "account_type")
        if account_type in ["Receivable", "Payable"]:
            row = {
                "account": payroll_payable_account,
                "debit_in_account_currency": flt(amount, precision),
                "exchange_rate": flt(exchange_rate),
                "reference_type": self.doctype,
                "reference_name": self.name,
                "party_type": "Employee",
                "party": party
            }
        else:
            row = {
                "account": payroll_payable_account,
                "debit_in_account_currency": flt(amount, precision),
                "exchange_rate": flt(exchange_rate),
                "reference_type": self.doctype,
                "reference_name": self.name
            }
        accounts.append(row)

        if len(currencies) > 1:
            multi_currency = 1

        journal_entry = frappe.new_doc('Journal Entry')
        journal_entry.voucher_type = 'Bank Entry'
        journal_entry.user_remark = _('Payment of {0} from {1} to {2}')\
            .format(user_remark, self.start_date, self.end_date)
        journal_entry.company = self.company
        journal_entry.posting_date = self.posting_date
        journal_entry.multi_currency = multi_currency

        journal_entry.set("accounts", accounts)
        journal_entry.save(ignore_permissions=True)


    def make_filters(self):
        filters = frappe._dict()
        filters['company'] = self.company
        filters['branch'] = self.branch
        filters['department'] = self.department
        filters['designation'] = self.designation
        filters['project'] = self.project
        return filters


class TYFDocument(Document):

    def set_new_name(self, force=False, set_name=None, set_child_names=True):
        """Calls `frappe.naming.set_new_name` for parent and child docs."""
        if self.flags.name_set and not force:
            return

            # If autoname has set as Prompt (name)
        if self.get("__newname"):
            self.name = self.get("__newname")
            self.flags.name_set = True
            return

        if set_name:
            self.name = set_name
        else:
            custom_set_new_name(self)

        if set_child_names:
            # set name for children
            for d in self.get_all_children():
                custom_set_new_name(d)

def custom_set_new_name(doc):
    """
    Sets the `name` property for the document based on various rules.

    1. If amended doc, set suffix.
    2. If `autoname` method is declared, then call it.
    3. If `autoname` property is set in the DocType (`meta`), then build it using the `autoname` property.
    4. If no rule defined, use hash.

    :param doc: Document to be named.
    """

    doc.run_method("before_naming")

    autoname = frappe.get_meta(doc.doctype).autoname or ""

    if autoname.lower() != "prompt" and not frappe.flags.in_import:
        doc.name = None

    if getattr(doc, "amended_from", None):
        doc.name = _get_amended_name(doc)
        return

    elif getattr(doc.meta, "issingle", False):
        doc.name = doc.doctype

    # elif getattr(doc.meta, "istable", False):
    # 	doc.name = make_autoname("hash", doc.doctype)

    if not doc.name:
        set_naming_from_document_naming_rule(doc)

    if not doc.name:
        doc.run_method("autoname")

    if not doc.name and autoname:
        set_name_from_naming_options(autoname, doc)

    # if the autoname option is 'field:' and no name was derived, we need to
    # notify
    if not doc.name and autoname.startswith("field:"):
        fieldname = autoname[6:]
        frappe.throw(_("{0} is required").format(
            doc.meta.get_label(fieldname)))

    # at this point, we fall back to name generation with the hash option
    if not doc.name and autoname == "hash":
        doc.name = make_autoname("hash", doc.doctype)

    if not doc.name:
        doc.name = make_autoname("hash", doc.doctype)

    doc.name = validate_name(
        doc.doctype,
        doc.name,
        frappe.get_meta(doc.doctype).get_field("name_case")
    ) 


def get_filter_condition(filters):
    cond = ''
    for f in ['company', 'branch', 'department', 'designation', 'project']:
        if filters.get(f):
            cond += " and t1." + f + " = " + frappe.db.escape(filters.get(f))

    return cond
