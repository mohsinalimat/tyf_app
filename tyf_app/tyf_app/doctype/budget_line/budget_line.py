# Copyright (c) 2021, aalfarran and contributors
# For license information, please see license.txt

import frappe
from frappe import _ 
from frappe.model.document import Document
from frappe.model.naming import _get_amended_name,  set_naming_from_document_naming_rule, make_autoname, set_name_from_naming_options, validate_name


class BudgetLine(Document):
	# def validate(self):
	# 	print("=== validate ===")

	def set_new_name(self, force=False, set_name=None, set_child_names=True):
		"""Calls `frappe.naming.set_new_name` for parent and child docs."""
		print("ITS TYF set_new_name")
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
    print("ITS TYF custom_set_new_name")
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


@frappe.whitelist()
def get_budget_line_doc(project_code):
	doc = frappe.new_doc('Budget Line')
	doc.project_code = project_code
	return doc

@frappe.whitelist()
def get_budget_doc(project_code):
	doc = frappe.new_doc('Budget')
	doc.budget_against = "Project"
	doc.project = project_code
	doc.set('accounts',get_budget_line_chiled(project_code))
	return doc

def get_budget_line_chiled(project_code):
	account_ditails = []
	parents = frappe.get_all(
		'Budget Line',
		filters={'project_code': project_code, 'docstatus': 1},
		fields=[
			'name'
			], order_by='code')
	for parent in parents:
		children = frappe.get_all(
			'Budget Line Child',
			filters={
				'parenttype': 'Budget Line',
				'parent': parent.name},
				fields=[
					'code',
					'total_cost',
					'account'
					], order_by='idx')

		for child in children:
			if child.account:
				if not account_ditails:
					account_ditails.append({
						"account": child.account,
						"budget_amount": child.total_cost
						})
				else:
					old = False
					for acc in account_ditails:
						if acc['account'] == child.account:
							acc['budget_amount'] += child.total_cost
							old = True
					if not old:
						account_ditails.append({
							"account": child.account,
							"budget_amount": child.total_cost
							})
	return account_ditails


@frappe.whitelist()
def get_budget_line(project_code, show_draft, show_cancelled):
	data = []
	parents = frappe.get_all(
		'Budget Line',
		filters={'project_code': project_code, 'docstatus': ['in', ['1', show_draft, show_cancelled]]},
		fields=[
			'code',
			'docstatus',
			'description',
			'name',
			'total_cost'
			], order_by='code')
	for parent in parents:
		data.append({
			"name": parent.name,
			"type": "parent",
			"code": parent.code,
			"status": parent.docstatus,
			"description": parent.description,
			"total_cost": frappe.format(parent.total_cost, 'Currency')
			})
		children = frappe.get_all(
			'Budget Line Child',
			filters={
				'parenttype': 'Budget Line',
				'parent': parent.name},
				fields=[
					'code',
					'title',
					'd_or_s',
					'sector',
					'quantity',
					'unit_cost',
					'duration',
					'charge',
					'total_cost'
					], order_by='idx')
		for child in children:
			for val in child:
				if child[val] is None:
					child[val] = "NA"
			data.append(
				{"type": "child",
				"code": child.code,
				"description": child.title,
				"d_or_s": child.d_or_s,
				"sector": child.sector,
				"quantity": child.quantity,
				"unit_cost": frappe.format(child.unit_cost, 'Currency'),
				"duration":child.duration,
				"charge": frappe.format(child.charge, 'Percent'),
				"total_cost": frappe.format(child.total_cost, 'Currency')
				})
	return data


@frappe.whitelist()
def get_footer(project_code, percent):
	data = []
	d_total = 0
	s_total = 0
	p_total = 0
	parents = frappe.get_all(
		'Budget Line',
		filters={'project_code': project_code, 'docstatus': 1},
		fields=[
			'name',
			'total_cost'
			], order_by='code')
	for parent in parents:
		p_total = p_total + parent.total_cost
		children = frappe.get_all(
			'Budget Line Child',
			filters={
				'parenttype': 'Budget Line',
				'parent': parent.name},
				fields=[
					'd_or_s',
					'total_cost'
					], order_by='idx')
		for child in children:
			if child.d_or_s == "D":
				d_total = d_total + child.total_cost
			else:
				s_total = s_total + child.total_cost

	data.append(
			{
			"tbody_id": "t_footer",
			"type": "Direct",
			"value": frappe.format(d_total, 'Currency')
			})
	data.append(
			{
			"tbody_id": "t_footer",
			"type": "Support",
			"value": frappe.format(s_total, 'Currency')	
			})
	data.append(
			{
			"tbody_id": "t_footer_psd",
			"type": "PSC Cost Percent",
			"value": frappe.format(percent, 'Percent')	
			})
	psc_ammount = p_total * (float(percent) / 100)
	data.append(
			{
			"tbody_id": "t_footer_psd",
			"type": "PSC Amount",
			"value": frappe.format(psc_ammount, 'Currency')	
			})
	data.append(
			{
			"tbody_id": "t_footer_psd",
			"type": "Total Cost",
			"value": frappe.format(psc_ammount + p_total, 'Currency'),
			"estimated_costing": psc_ammount + p_total
			})
	return data

@frappe.whitelist()
def get_latest_parent_code(project_code):
	max = 0
	parents = frappe.get_all(
		'Budget Line',
		filters={'project_code': project_code, 'docstatus': ['<', 2]},
		fields=[
			'code'
			], order_by='code')
	if parents:
		max = parents[0].code
		for i in range(len(parents)):
			if max < parents[i].code:
				max = parents[i].code
	return int(max) + 1

@frappe.whitelist()
def get_amended_doc_code(doc_name):
	amended = frappe.db.get_value(
		'Budget Line',
		doc_name,
		['code']
	)
	return amended

@frappe.whitelist()
def delete_amended_from_doc(doc_name):
	frappe.delete_doc("Budget Line", doc_name)

@frappe.whitelist()
def get_bl_account(bl_name):
	account = frappe.db.get_value(
		'Budget Line Child',
		bl_name,
		['account']
	)
	return account
