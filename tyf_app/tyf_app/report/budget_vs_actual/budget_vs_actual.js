// Copyright (c) 2016, Tamdeen Youth Foundation and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Budget Vs Actual"] = {
	"filters": [
		{
			fieldname: "from_fiscal_year",
			label: __("From Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: frappe.sys_defaults.fiscal_year,
			reqd: 1
		},
		{
			fieldname: "to_fiscal_year",
			label: __("To Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: frappe.sys_defaults.fiscal_year,
			reqd: 1
		},
		{
			fieldname: "period",
			label: __("Period"),
			fieldtype: "Select",
			options: [
				{ "value": "Monthly", "label": __("Monthly") },
				{ "value": "Quarterly", "label": __("Quarterly") },
				{ "value": "Half-Yearly", "label": __("Half-Yearly") },
				{ "value": "Yearly", "label": __("Yearly") }
			],
			default: "Yearly",
			reqd: 1
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "budget_against",
			label: __("Budget Against"),
			fieldtype: "Select",
			options: ["Cost Center", "Project"],
			default: "Cost Center",
			reqd: 1,
			on_change: function() {
				frappe.query_report.set_filter_value("budget_against_filter", []);
				frappe.query_report.refresh();
				
			}
		},
		{
			fieldname:"budget_against_filter",
			label: __('Dimension Filter'),
			fieldtype: "Dynamic Link",
			get_options: function() {
				let budget_against = frappe.query_report.get_filter_value('budget_against');
				return budget_against;
			}
		},
		{
			fieldname: "currency",
			label: __("Currency"),
			fieldtype: "Link",
			options: "Currency",
			default: frappe.defaults.get_default("currency")	
		},
		{
			fieldname:"show_cumulative",
			label: __("Show Cumulative Amount"),
			fieldtype: "Check",
			default: 0,
		},
	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if(data){

			if (column.fieldname.includes('variance')) {

				if (data[column.fieldname] < 0) {
					value = "<span style='color:red'>" + value + "</span>";
				}
				else if (data[column.fieldname] > 0) {
					value = "<span style='color:green'>" + value + "</span>";
				}
			}
		}

		return value;
	}
}

erpnext.dimension_filters.forEach((dimension) => {
	frappe.query_reports["Budget Vs Actual"].filters[4].options.push(dimension["document_type"]);
});
