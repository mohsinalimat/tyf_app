import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry
from erpnext.controllers.accounts_controller import set_balance_in_account_currency
from erpnext.accounts.utils import get_account_currency, get_fiscal_years
from frappe.model.document import Document
# from frappe.model.naming import _get_amended_name,  set_naming_from_document_naming_rule, make_autoname, set_name_from_naming_options, validate_name
import frappe
from frappe.utils import (
    flt,
    formatdate,
)
from frappe import _


class TYFPayrollEntry(PayrollEntry):

    def get_salary_components(self, component_type):
        salary_slips = self.get_sal_slip_list(ss_status=1, as_dict=True)
        if salary_slips:
            salary_components = frappe.db.sql("""
				select ssd.salary_component, ssd.amount, ssd.parentfield, ss.payroll_cost_center, ss.employee, ss.start_date, ss.end_date
				from `tabSalary Slip` ss, `tabSalary Detail` ssd
				where ss.name = ssd.parent and ssd.parentfield = '%s' and ss.name in (%s)
			""" % (component_type, ', '.join(['%s']*len(salary_slips))),
                tuple([d.name for d in salary_slips]), as_dict=True)
            if not self.is_shared_salary:
                return salary_components
            return self.set_salary_ammount(salary_components)

    def set_salary_ammount(self, salary_slips):

        """
        This method by Eng.Ibraheem Morghim and its for
        set salary ammount with project and budget line account dimention
        """

        salary_slips_with_project = []

        for i in salary_slips:
            projects = None
            payroll_details = frappe.get_list(
                "Employee Payroll Details",
                filters = {
                    "docstatus": 1,
                    "employee": i["employee"],
                    "from_date": ["<=", i["start_date"]],
                    "to_date": [">=", i["end_date"]],
                },
                fields = [
                    "name",
                    "company_share",
                    "company_cost_center"
                ],
            )
            if payroll_details:
                projects = frappe.get_list(
                    "Project Share",
                    filters = {
                        "parent": payroll_details[0]["name"]
                        },
                    fields = [
                        "project",
                        "budget_line",
                        "account",
                        "cost_center",
                        "share"
                        ],
                )
            if projects:
                amount = i["amount"]
                if payroll_details[0]["company_share"] > 0:
                    sal_slip = i.copy()
                    sal_slip["amount"] = amount * (payroll_details[0]["company_share"] / 100)
                    sal_slip["payroll_cost_center"] = payroll_details[0]["company_cost_center"]
                    salary_slips_with_project.append(sal_slip)
                    
                for p in projects:
                    sal_slip = i.copy()
                    sal_slip["amount"] = amount * (p["share"] / 100)
                    sal_slip["project"] = p["project"]
                    sal_slip["budget_line"] = p["budget_line"]
                    sal_slip["payroll_cost_center"] = p["cost_center"]
                    salary_slips_with_project.append(sal_slip)
            else:
                frappe.throw(
                    _("You have checked 'Is Shared Salary' and there is no 'Employee Payroll Details' for employee: {0}")
                        .format(frappe.bold(i["employee"]))
                    + "<br><br>" + _("Pleas make sure to create one and submet it first."),
                    title=_("Error")
                )
                # salary_slips_with_project.append(i)

        return salary_slips_with_project

    def get_salary_component_total(self, component_type=None):
        salary_components = self.get_salary_components(component_type)
        if salary_components:
            component_dict = {}
            for item in salary_components:
                add_component_to_accrual_jv_entry = True
                if component_type == "earnings":
                    is_flexible_benefit, only_tax_impact = frappe.db.get_value(
                        "Salary Component",
                        item['salary_component'],
                        ['is_flexible_benefit', 'only_tax_impact'])
                    if is_flexible_benefit == 1 and only_tax_impact == 1:
                        add_component_to_accrual_jv_entry = False
                if add_component_to_accrual_jv_entry:
                    if item.project:
                        component_dict[
                            (
                                item.salary_component,
                                item.payroll_cost_center,
                                item.project,
                                item.budget_line,
                                item.employee
                                
                            )
                        ] = component_dict.get(
                            (
                                item.salary_component,
                                item.payroll_cost_center,
                                item.project,
                                item.budget_line,
                                item.employee),
                                0
                            ) + flt(item.amount)
                    else:
                        component_dict[
                            (
                                item.salary_component,
                                item.payroll_cost_center,
                                item.employee
                                
                            )
                        ] = component_dict.get(
                            (
                                item.salary_component,
                                item.payroll_cost_center,
                                item.employee),
                                0
                            ) + flt(item.amount)

            account_details = self.get_account(component_dict=component_dict)
            return account_details

    def get_account(self, component_dict=None):
        account_dict = {}
        for key, amount in component_dict.items():
            account = self.get_salary_component_account(key[0])
            i = 1
            key_dict = [account]
            while i < len(key):
                key_dict.append(key[i])
                i += 1
            account_dict[tuple(key_dict)] = account_dict.get(
                tuple(key_dict), 0) + amount
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

            # Earnings
            for acc_cc, amount in earnings.items():
                exchange_rate, amt = self.get_amount_and_exchange_rate_for_journal_entry(
                    acc_cc[0], amount, company_currency, currencies)
                payable_amount += flt(amount, precision)
                account_type = frappe.db.get_value(
                    "Account", acc_cc[0], "account_type")
                if account_type in ["Receivable", "Payable"]:
                    if self.is_shared_salary and len(acc_cc) > 3:
                        row = {
                            "account": acc_cc[0],
                            "debit_in_account_currency": flt(amt, precision),
                            "exchange_rate": flt(exchange_rate),
                            "cost_center": acc_cc[1] or self.cost_center,
                            "project": acc_cc[2],
                            "budget_line_child": str(acc_cc[3]),
                            "party_type": "Employee",
                            "party": acc_cc[4]
                        }
                    else:
                        row = {
                            "account": acc_cc[0],
                            "debit_in_account_currency": flt(amt, precision),
                            "exchange_rate": flt(exchange_rate),
                            "cost_center": acc_cc[1] or self.cost_center,
                            "project": self.project,
                            "party_type": "Employee",
                            "party": acc_cc[2]
                        }
                else:
                    if self.is_shared_salary and len(acc_cc) > 3:
                        row = {
                            "account": acc_cc[0],
                            "debit_in_account_currency": flt(amt, precision),
                            "exchange_rate": flt(exchange_rate),
                            "cost_center": acc_cc[1] or self.cost_center,
                            "project": acc_cc[2],
                            "budget_line_child": acc_cc[3]
                        }
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
                    if self.is_shared_salary and len(acc_cc) > 3:
                        row = {
                            "account": acc_cc[0],
                            "credit_in_account_currency": flt(amt, precision),
                            "exchange_rate": flt(exchange_rate),
                            "cost_center": acc_cc[1] or self.cost_center,
                            "project": acc_cc[2],
                            "budget_line_child": acc_cc[3],
                            "party_type": "Employee",
                            "party": acc_cc[4]
                        }
                    else:
                        row = {
                            "account": acc_cc[0],
                            "credit_in_account_currency": flt(amt, precision),
                            "exchange_rate": flt(exchange_rate),
                            "cost_center": acc_cc[1] or self.cost_center,
                            "project": self.project,
                            "party_type": "Employee",
                            "party": acc_cc[2]
                        }
                else:
                    if self.is_shared_salary and len(acc_cc) > 3:
                        row = {
                            "account": acc_cc[0],
                            "credit_in_account_currency": flt(amt, precision),
                            "exchange_rate": flt(exchange_rate),
                            "cost_center": acc_cc[1] or self.cost_center,
                            "project": acc_cc[2],
                            "budget_line_child": str(acc_cc[3])
                        }
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


    def update_accounting_dimensions(self, row, accounting_dimensions):
        for dimension in accounting_dimensions:
           if self.get(dimension):
                row.update({dimension: self.get(dimension)})
        return row


    # def make_filters(self):
    #     filters = frappe._dict()
    #     filters['company'] = self.company
    #     filters['branch'] = self.branch
    #     filters['department'] = self.department
    #     filters['designation'] = self.designation
    #     filters['project'] = self.project
    #     return filters

# class TYFJournalEntry(JournalEntry):
#     def make_gl_entries(self, cancel=0, adv_adj=0):
#         from erpnext.accounts.general_ledger import make_gl_entries

#         gl_map = []
#         for d in self.get("accounts"):
#             if d.debit or d.credit:
#                 r = [d.user_remark, self.remark]
#                 r = [x for x in r if x]
#                 remarks = "\n".join(r)

#                 gl_map.append(
#                     self.get_gl_dict({
#                         "account": d.account,
#                         "party_type": d.party_type,
#                         "due_date": self.due_date,
#                         "party": d.party,
#                         "budget_line_child": d.budget_line,
#                         "against": d.against_account,
#                         "debit": flt(d.debit, d.precision("debit")),
#                         "credit": flt(d.credit, d.precision("credit")),
#                         "account_currency": d.account_currency,
#                         "debit_in_account_currency": flt(d.debit_in_account_currency, d.precision("debit_in_account_currency")),
#                         "credit_in_account_currency": flt(d.credit_in_account_currency, d.precision("credit_in_account_currency")),
#                         "against_voucher_type": d.reference_type,
#                         "against_voucher": d.reference_name,
#                         "remarks": remarks,
#                         "voucher_detail_no": d.reference_detail_no,
#                         "cost_center": d.cost_center,
#                         "project": d.project,
#                         "finance_book": self.finance_book
#                     }, item=d)
#                 )

#         if self.voucher_type in ('Deferred Revenue', 'Deferred Expense'):
#             update_outstanding = 'No'
#         else:
#             update_outstanding = 'Yes'

#         if gl_map:
#             make_gl_entries(gl_map, cancel=cancel, adv_adj=adv_adj, update_outstanding=update_outstanding)


# def set_new_name(self, force=False, set_name=None, set_child_names=True):
#     """Calls `frappe.naming.set_new_name` for parent and child docs."""
#     print("ITS TYF set_new_name")
#     if self.flags.name_set and not force:
#         return

#         # If autoname has set as Prompt (name)
#     if self.get("__newname"):
#         self.name = self.get("__newname")
#         self.flags.name_set = True
#         return

#     if set_name:
#         self.name = set_name
#     else:
#         custom_set_new_name(self)

#     if set_child_names:
#         # set name for children
#         for d in self.get_all_children():
            
#             custom_set_new_name(d)


# def custom_set_new_name(doc):
#     print("ITS TYF custom_set_new_name")
#     """
#     Sets the `name` property for the document based on various rules.

#     1. If amended doc, set suffix.
#     2. If `autoname` method is declared, then call it.
#     3. If `autoname` property is set in the DocType (`meta`), then build it using the `autoname` property.
#     4. If no rule defined, use hash.

#     :param doc: Document to be named.
#     """

#     doc.run_method("before_naming")

#     autoname = frappe.get_meta(doc.doctype).autoname or ""

#     if autoname.lower() != "prompt" and not frappe.flags.in_import:
#         doc.name = None

#     if getattr(doc, "amended_from", None):
#         doc.name = _get_amended_name(doc)
#         return

#     elif getattr(doc.meta, "issingle", False):
#         doc.name = doc.doctype

#     # elif getattr(doc.meta, "istable", False):
#     # 	doc.name = make_autoname("hash", doc.doctype)

#     if not doc.name:
#         set_naming_from_document_naming_rule(doc)

#     if not doc.name:
#         doc.run_method("autoname")

#     if not doc.name and autoname:
#         set_name_from_naming_options(autoname, doc)

#     # if the autoname option is 'field:' and no name was derived, we need to
#     # notify
#     if not doc.name and autoname.startswith("field:"):
#         fieldname = autoname[6:]
#         frappe.throw(_("{0} is required").format(
#             doc.meta.get_label(fieldname)))

#     # at this point, we fall back to name generation with the hash option
#     if not doc.name and autoname == "hash":
#         doc.name = make_autoname("hash", doc.doctype)

#     if not doc.name:
#         doc.name = make_autoname("hash", doc.doctype)

#     doc.name = validate_name(
#         doc.doctype,
#         doc.name,
#         frappe.get_meta(doc.doctype).get_field("name_case")
#     ) 


# def get_filter_condition(filters):
#     cond = ''
#     for f in ['company', 'branch', 'department', 'designation', 'project']:
#         if filters.get(f):
#             cond += " and t1." + f + " = " + frappe.db.escape(filters.get(f))

#     return cond

# def get_gl_dict(self, args, account_currency=None, item=None):
#     """this method populates the common properties of a gl entry record"""
#     # print("Its TYF")
#     posting_date = args.get('posting_date') or self.get('posting_date')
#     fiscal_years = get_fiscal_years(posting_date, company=self.company)
#     if len(fiscal_years) > 1:
#         frappe.throw(_("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
#             formatdate(posting_date)))
#     else:
#         fiscal_year = fiscal_years[0][0]

#     gl_dict = frappe._dict({
#         'company': self.company,
#         'posting_date': posting_date,
#         'fiscal_year': fiscal_year,
#         'voucher_type': self.doctype,
#         'voucher_no': self.name,
#         'remarks': self.get("remarks") or self.get("remark"),
#         'debit': 0,
#         'credit': 0,
#         'debit_in_account_currency': 0,
#         'credit_in_account_currency': 0,
#         'is_opening': self.get("is_opening") or "No",
#         'party_type': None,
#         'party': None,
#         'budget_line': self.get("budget_line"),
#         'project': self.get("project")
#     })

#     accounting_dimensions = get_accounting_dimensions()
#     dimension_dict = frappe._dict()

#     for dimension in accounting_dimensions:
#         dimension_dict[dimension] = self.get(dimension)
#         if item and item.get(dimension):
#             dimension_dict[dimension] = item.get(dimension)

#     gl_dict.update(dimension_dict)
#     gl_dict.update(args)

#     if not account_currency:
#         account_currency = get_account_currency(gl_dict.account)

#     if gl_dict.account and self.doctype not in ["Journal Entry",
#         "Period Closing Voucher", "Payment Entry", "Purchase Receipt", "Purchase Invoice", "Stock Entry"]:
#         self.validate_account_currency(gl_dict.account, account_currency)

#     if gl_dict.account and self.doctype not in ["Journal Entry", "Period Closing Voucher", "Payment Entry"]:
#         set_balance_in_account_currency(gl_dict, account_currency, self.get("conversion_rate"),
#                                         self.company_currency)

#     return gl_dict