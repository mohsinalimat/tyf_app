frappe.ui.form.on("Project", {
  refresh: function (frm) {
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
      
    if (!frm.doc.__islocal){ 
      frm.events.get_budget_line(frm);
      frm.events.get_footer(frm);
      $(frm.fields_dict['bl_html'].wrapper)
      .html(frappe.render_template(html));
    } else {
      console.log("I am just created w8ing to be saved")
       $(frm.fields_dict['bl_html'].wrapper).empty()
   }
  },

  psc_cost_percent: (frm) => {
    cur_frm.refresh();
  },

  new_budget_line: (frm) => {
    var cur_frm_name = frm.doc.name;
    frappe.call({
      method: 'tyf_app.tyf_app.doctype.budget_line.budget_line.get_budget_line_doc',
      args : {
        'project_code': cur_frm_name
      },
      callback: function(r) {
        var doc = frappe.model.sync(r.message);
        frappe.set_route("Form", r.message.doctype, r.message.name);
      }
    });
  },
  
  add_row:(frm, data) => {
    for(let i=0 ; i < data.length ; i++){
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
        cell.colSpan = "7";
        cell.innerHTML= data[i].description;
        row.insertCell(2).innerHTML= data[i].total_cost;
        row.insertCell(3).className = "td_edit_btn_" + i;
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
      'project_code': frm.doc.name
    }).then(r => {
      frm.events.add_row(frm, r);
    });
  },

  get_footer:(frm) => {
    frappe.xcall('tyf_app.tyf_app.doctype.budget_line.budget_line.get_footer', {
      'project_code': frm.doc.name,
      'percent': frm.doc.psc_cost_percent
    }).then(r => {
      frm.events.add_row_footer(frm, r);
    });
  },

});
