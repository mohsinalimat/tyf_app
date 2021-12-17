frappe.ui.form.on("Project", {
  refresh: function (frm) {
    if (!frm.doc.__islocal){
      frm.events.table_render(frm);
    } else {
       $(frm.fields_dict['bl_html'].wrapper).empty()
    }
    frm.events.set_create_budget_button(frm);
  },

  set_create_budget_button: (frm) => {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Create Budget'), () => {
				frm.events.create_budget(frm);
			});
		}
	},

  psc_cost_percent: (frm) => {
    cur_frm.refresh();
  },

  show_draft_budget_lines: (frm) => {
    frm.events.table_render(frm);
  },

  show_cancelled_budget_lines: (frm) => {
    frm.events.table_render(frm);
  },

  new_budget_line: (frm) => {
    var cur_frm_name = frm.doc.name;
    frappe.call({
      method: 'tyf_app.tyf_app.doctype.budget_line.budget_line.get_budget_line_doc',
      args : {
        'project_code': cur_frm_name
      },
      callback: (r) => {
        var doc = frappe.model.sync(r.message);
        frappe.set_route("Form", doc[0].doctype, doc[0].name);
      }
    });
  },

  create_budget: (frm) => {
    var cur_frm_name = frm.doc.name;
    frappe.call({
      method: 'tyf_app.tyf_app.doctype.budget_line.budget_line.get_budget_doc',
      args : {
        'project_code': cur_frm_name
      },
      callback: (r) => {        
        var doc = frappe.model.sync(r.message);
        frappe.set_route("Form", doc[0].doctype, doc[0].name);
      }
    });
  },
  
  add_row:(frm, data) => {
    for(let i=0 ; i < data.length ; i++){
      var status = undefined;
      if (data[i].status == 2){
        status = `
        <span class="indicator-pill red filterable ellipsis" >
				<span class="ellipsis"> Cancelled</span>
			  <span>
				</span></span>
        `
      } else if (data[i].status == 1) {
        status = `
        <span class="indicator-pill green filterable ellipsis" >
				<span class="ellipsis"> Submeted</span>
			  <span>
				</span></span>
        `
      } else {
        status = `
        <span class="indicator-pill yellow filterable ellipsis" >
				<span class="ellipsis"> Draft</span>
			  <span>
				</span></span>
        `
      }
      var btn = document.createElement('input');
      btn.type = "button";
      btn.className = "btn";
      btn.value = "Edit";
      btn.onclick = () => {frappe.set_route("Form", "Budget Line", data[i].name);};
      var table = document.getElementById('t_body')
      var rowCount = table.rows.length;
      var row = table.insertRow(rowCount);
      if (data[i].type == "parent"){
        row.id = "t_parent";
        row.insertCell(0).innerHTML= data[i].code;
        var cell = row.insertCell(1);
        cell.colSpan = "5";
        cell.innerHTML= data[i].description;
        var cell2 = row.insertCell(2);
        cell2.colSpan = "2";
        cell2.style = "text-align: center;";
        cell2.innerHTML= status;
        row.insertCell(3).innerHTML= data[i].total_cost;
        row.insertCell(4).className = "td_edit_btn_" + i;
        var td = document.getElementsByClassName("td_edit_btn_" + i);
        td[0].appendChild(btn);
      } else {
        row.id = "t_child";
        row.insertCell(0).innerHTML= data[i].code;
        row.insertCell(1).innerHTML= data[i].description;
        row.insertCell(2).innerHTML= data[i].d_or_s;
        row.insertCell(3).innerHTML= data[i].sector;
        row.insertCell(4).innerHTML= data[i].quantity;
        row.insertCell(5).innerHTML= data[i].unit_cost;
        row.insertCell(6).innerHTML= data[i].duration;
        row.insertCell(7).innerHTML= data[i].charge;
        var cell = row.insertCell(8);
        cell.colSpan = "2";
        cell.innerHTML= data[i].total_cost;
      }
    }
  },

  add_row_footer:(frm, data) => {
    
    for(let i=0 ; i < data.length ; i++){
      var table = document.getElementById(data[i].tbody_id)
      var rowCount = table.rows.length;
      var row = table.insertRow(rowCount);
      var type_cell = row.insertCell(0);
      var total_cell = row.insertCell(1);
      type_cell.colSpan = "8";
      type_cell.innerHTML = data[i].type;
      total_cell.colSpan = "2";
      total_cell.innerHTML = data[i].value;
      if(data[i].type == "Total Cost"){
        frm.set_value("estimated_costing", data[i].estimated_costing);
      }
    }
  },
  
  get_budget_line:(frm) => {
    frappe.xcall('tyf_app.tyf_app.doctype.budget_line.budget_line.get_budget_line', {
      'project_code': frm.doc.name,
      'show_draft': frm.doc.show_draft_budget_lines ? "0" : "1",
      'show_cancelled': frm.doc.show_cancelled_budget_lines ? "2" : "1"
    }).then(r => {
      frm.events.add_row(frm, r);
      refresh_field('bl_html');
    });
  },

  get_footer:(frm) => {
    frappe.xcall('tyf_app.tyf_app.doctype.budget_line.budget_line.get_footer', {
      'project_code': frm.doc.name,
      'percent': frm.doc.psc_cost_percent
    }).then(r => {
      frm.events.add_row_footer(frm, r);
      refresh_field('bl_html');
    });
  },

  table_render: (frm) => {
    var html =
      `
      <hr>
      <table>
          <thead>
            <tr>
            <th id="bl-code">Code</th>
            <th id="bl-desc">Budget Line Description</th>
            <th id="bl-ds">D / S</th>
            <th id="bl-sector">Sector</th>
            <th id="bl-quantity">Qty</th>
            <th id="bl-cost">Unit cost</th>
            <th id="bl-duration">Duration</th>
            <th id="bl-percent">% Cost</th>
            <th id="bl-total">Total Cost</th>
            <th id="bl-total">Edit</th>
            </tr>
          </thead>
          <tbody id="t_body">
            
          </tbody>
          <thead>
            <tr>
            <th colspan="8">SubTotal</th>
            <th colspan="2">Ammount</th>
            </tr>
          </thead>
          <tbody id="t_footer">
            
          </tbody>
          <thead>
            <tr>
            <th colspan="10">PSC Cost</th>
            </tr>
          </thead>
          <tbody id="t_footer_psd">
            
          </tbody>
      </table>
      
      `;
      
     
      frm.events.get_budget_line(frm);
      frm.events.get_footer(frm);
      $(frm.fields_dict['bl_html'].wrapper)
      .html(frappe.render_template(html));
  }

});
