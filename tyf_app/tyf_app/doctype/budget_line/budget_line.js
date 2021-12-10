// Copyright (c) 2021, aalfarran and contributors
// For license information, please see license.txt

frappe.ui.form.on('Budget Line', {

	refresh: function(frm) {
		if (frm.is_new() && frm.doc.amended_from){
			
			// frm.set_value
		}
		frm.fields_dict['bl_child'].grid.get_field('account').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			return {    
				filters:[
					['is_group', '=', 0]
				]
			}
		}
	},

	// before_save: (frm) => {
	// 	if(frm.doc.amended_from){
	// 		frm.set_value("amended_from", undefined);
	// 	}
	// },
	validate: (frm) => {
		if (frm.doc.amended_from){
			frappe.xcall('tyf_app.tyf_app.doctype.budget_line.budget_line.delete_amended_from_doc', {
				'doc_name': frm.doc.amended_from
			  }).then(r => {
				frm.set_value("amended_from", undefined);
			  });
		}
	},
	onload: (frm) => {
		if(frm.doc.project_code && frm.doc.__islocal){
			if(frm.doc.amended_from){
				frm.events.get_amended_doc_code(frm);
			} else {
				frm.events.get_max_parent_code(frm);
			}
		}
	},

	project_code: (frm) => {
		if(frm.doc.amended_from){
			frm.set_value("amended_from", undefined);
		}
		if(frm.doc.project_code){
			frm.events.get_max_parent_code(frm);
		} else {
			frm.set_value("code", undefined);
		}
	},

	code: (frm) => {
		if (frm.doc.code == ''){
			frm.set_value("code", undefined);
		}
	},

	increase_counter: (frm) => {
		frm.set_value("counter", frm.doc.counter + 1);
	},
	decrease_counter: (frm) => {
		frm.set_value("counter", frm.doc.counter - 1);
	},
	

	remove_child: (frm) => {
		var tbl = frm.doc.bl_child || [];
		var i = tbl.length;
		while (i--)
		{
			if(tbl[i].code == undefined)
			{
				cur_frm.get_field("bl_child").grid.grid_rows[i].remove();
			}
		}
		cur_frm.refresh();
	},
	calculate_total_cost: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "total_cost", ((row.quantity * row.unit_cost) * row.duration) * (row.charge / 100));
		frm.events.calculate_parent_total_cost(frm, cdt, cdn);
	},

	calculate_parent_total_cost: (frm, cdt, cdn) => {
		var tbl = frm.doc.bl_child || [];
		var i = tbl.length;
		var total = 0;
		while (i--)
		{
			total = total + tbl[i].total_cost;
		}
		frm.set_value("total_cost", total);
	},
	recalculate_child_code: (frm, cdt, cdn) => {
		var tbl = frm.doc.bl_child || [];
		var i = tbl.length;
		var total = 0;
		while (i--)
		{
			tbl[i].code;
			var j = i+1;
			cur_frm.get_field("bl_child").grid.grid_rows[i].doc.code = frm.doc.code + "." + j;
		}
		cur_frm.refresh();
	},

	get_max_parent_code: (frm) => {
		frappe.xcall('tyf_app.tyf_app.doctype.budget_line.budget_line.get_latest_parent_code', {
			'project_code': frm.doc.project_code
		  }).then(r => {
			frm.set_value("code", r);
		  });
	},

	get_amended_doc_code: (frm) => {
		frappe.xcall('tyf_app.tyf_app.doctype.budget_line.budget_line.get_amended_doc_code', {
			'doc_name': frm.doc.amended_from
		  }).then(r => {
			frm.set_value("code", r);
		  });
	}
});




frappe.ui.form.on("Budget Line Child", {

	quantity: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		if(row.quantity == ''){
			frappe.model.set_value(cdt, cdn, "quantity", 0);
			cur_frm.refresh();
		}
		frm.events.calculate_total_cost(frm, cdt, cdn);

	},

	unit_cost: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		if(row.unit_cost == ''){
			frappe.model.set_value(cdt, cdn, "unit_cost", 0);
			cur_frm.refresh();
		}
		frm.events.calculate_total_cost(frm, cdt, cdn);

	},

	duration: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		if(row.duration == ''){
			frappe.model.set_value(cdt, cdn, "duration", 0);
			cur_frm.refresh();
		}
		frm.events.calculate_total_cost(frm, cdt, cdn);

	},

	charge: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		if(row.charge == ''){
			frappe.model.set_value(cdt, cdn, "charge", 0);
			cur_frm.refresh();
		}
		frm.events.calculate_total_cost(frm, cdt, cdn);

	},
  
	bl_child_add: function(frm, cdt, cdn) {
		if (frm.doc.project_code){
			frappe.model.set_value(cdt, cdn, "project_code", frm.doc.project_code);
		}
		if(frm.doc.code != undefined){
			var idx = locals[cdt][cdn].idx;
			frappe.model.set_value(cdt, cdn, "code", frm.doc.code + "." + idx);
			frm.events.increase_counter(frm);
		} else {
			frm.events.remove_child(frm);
			frappe.throw(__("Please insert 'Code' value first."));	
		}
	},
  
	bl_child_remove: function(frm, cdt, cdn) {
		if (frm.doc.bl_child == ""){
			frm.set_value("bl_child", undefined);
		}
		frm.events.decrease_counter(frm);
		frm.events.calculate_parent_total_cost(frm, cdt, cdn);
		frm.events.recalculate_child_code(frm, cdt, cdn);
	},
  
});