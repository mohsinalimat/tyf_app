# Copyright (c) 2021, aalfarran and contributors
# For license information, please see license.txt

import frappe
from frappe import _ 
from frappe.model.document import Document

class BudgetLine(Document):
	def validate(self):
		print("=== validate ===")
		frappe.msgprint(_("is active"))


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