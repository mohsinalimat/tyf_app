# Copyright (c) 2021, Tamdeen Youth Foundation and contributors
# For license information, please see license.txt

# This class writen by Eng.Ibraheem Morghim


import frappe
from frappe.model.document import Document
from frappe import _, throw

class EmployeePayrollDetails(Document):

    def validate(self):
        self.validate_share_percentage()
        self.validate_project()
        self.validate_dates()

    def validate_dates(self):
        employee_project = frappe.get_list(
			"Employee Payroll Details",
			filters = {
				"docstatus": 1,
				"employee": self.employee,
				"from_date": ["<=", self.from_date],
				"to_date": [">=", self.to_date]
			},
			fields=["name"]
		)
        if employee_project:
            throw(
				_("There is overlaping with another 'Employee Projects Payroll': {0}.")
				.format(frappe.bold(employee_project.name)))

    def validate_share_percentage(self):
        total_percentage = self.company_share
        for i in self.project_share:
            total_percentage = total_percentage + i.share
        if total_percentage != 100:
            throw(_("Total of 'Share (%)' for all 'Projects' and 'Company Share (%)' can not be more or less than 100 %."))

    def validate_project(self):
        projects = []
        for i in self.project_share:
            if i.project in projects:
                throw(_("There is duplicate on 'Project': {0}.").format(frappe.bold(i.project)))
            projects.append(i.project)



