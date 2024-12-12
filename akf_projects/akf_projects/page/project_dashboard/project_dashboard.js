
// let filters = {};
// frappe.pages['project-dashboard'].on_page_load = async function(wrapper) {
// 	var page = frappe.ui.make_app_page({
// 		parent: wrapper,
// 		title: 'Project Dashboard',
// 		single_column: true
// 	});
// 	await filters.add(page);
// }


frappe.pages['project-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Project Dashboard',
        single_column: true
    });

    server_call.fetch_data(page);
};


server_call = {
    fetch_data: function(page) {
        frappe.call({
            method: "akf_projects.akf_projects.page.project_dashboard.project_dashboard.get_information",
            args: {},
            callback: function(r) {
				
                var info = r.message;
                console.log(info);

                // Render new content
                // $(frappe.render_template("project_survey_dashboard", {
                //     'region_wise_survey': info['region_wise_survey'],
                // })).appendTo(page.main);
				$(frappe.render_template("project_dashboard", r.message)).appendTo(page.main);

                _highcharts_.load_charts(info);
                // console.log(r.message);

            },
        });
    },
	
};



_highcharts_ = {
    load_charts: function (info) {      
      _highcharts_.region_wise_survey(info.region_wise_survey);     
      _highcharts_.district_wise_survey(info.district_wise_survey);     
      _highcharts_.tehsil_wise_survey(info.tehsil_wise_survey);     
      _highcharts_.product_wise_survey(info.product_wise_survey);     
      _highcharts_.project_status(info.project_status);     
      _highcharts_.approved_vs_unapproved_projects(info.approved_vs_unapproved_projects);     
    },

    region_wise_survey: function (data) {
        let chart_js = region_wise_survey_(data)
        $("#region_wise_survey").html(chart_js)
    }, 

    district_wise_survey: function (data) {
        let chart_js = district_wise_survey_(data)
        $("#district_wise_survey").html(chart_js)
    }, 

    tehsil_wise_survey: function (data) {
        let chart_js = tehsil_wise_survey_(data)
        $("#tehsil_wise_survey").html(chart_js)
    }, 

    product_wise_survey: function (data) {
        let chart_js = product_wise_survey_(data)
        $("#product_wise_survey").html(chart_js)
    }, 

    project_status: function (data) {
        let chart_js = project_status_(data)
        $("#project_status").html(chart_js)
    }, 

    approved_vs_unapproved_projects: function (data) {
        let chart_js = approved_vs_unapproved_projects_(data)
        $("#approved_vs_unapproved_projects").html(chart_js)
    }, 
     
};

function region_wise_survey_(data) {
	
    return `
    <script>

	Highcharts.chart('region_wise_survey', {
		chart: {
			type: 'pie',
			options3d: {
				enabled: true,
				alpha: 45,
				beta: 0
			}
		},
		title: {
			text: 'Region Wise Projects',
			align: 'left'
		},
		subtitle: {
			text: null
		},
		plotOptions: {
			pie: {
				allowPointSelect: true,
				cursor: 'pointer',
				depth: 35,
				dataLabels: {
					enabled: true,
					format: '{point.name}: {y}'
				}
			}
		},
		series: [{
			type: 'pie',
			name: 'Region',
			data: ${JSON.stringify(data.data)},
		}],
		credits: {
			enabled: false 
		}
	});
	</script>
    `
}

function district_wise_survey_(data) {
	
    return `
    <script>

	Highcharts.chart('district_wise_survey', {
		chart: {
			type: 'pie',
			options3d: {
				enabled: true,
				alpha: 45,
				beta: 0
			}
		},
		title: {
			text: 'District Wise Projects',
			align: 'left'
		},
		subtitle: {
			text: null
		},
		plotOptions: {
			pie: {
				allowPointSelect: true,
				cursor: 'pointer',
				depth: 35,
				dataLabels: {
					enabled: true,
					format: '{point.name}: {y}'
				}
			}
		},
		series: [{
			type: 'pie',
			name: 'Region',
			data: ${JSON.stringify(data.data)},
		}],
		credits: {
			enabled: false 
		}
	});
	</script>
    `
}


function tehsil_wise_survey_(data) {
	
    return `
    <script>

	Highcharts.chart('tehsil_wise_survey', {
		chart: {
			type: 'pie',
			options3d: {
				enabled: true,
				alpha: 45,
				beta: 0
			}
		},
		title: {
			text: 'Tehsil Wise Projects',
			align: 'left'
		},
		subtitle: {
			text: null
		},
		plotOptions: {
			pie: {
				innerSize: 100,
				depth: 45,
				dataLabels: {
					enabled: true,
					format: '{point.name}: {y}'
				}
			}
		},
		series: [{
			type: 'pie',
			name: 'Region',
			data: ${JSON.stringify(data.data)},
		}],
		credits: {
			enabled: false 
		}
	});
	</script>
    `
}

function product_wise_survey_(data) {
	
    return `
    <script>

	Highcharts.chart('product_wise_survey', {
		chart: {
			type: 'pie',
			options3d: {
				enabled: true,
				alpha: 45,
				beta: 0
			}
		},
		title: {
			text: 'Product Wise Projects',
			align: 'left'
		},
		subtitle: {
			text: null
		},
		plotOptions: {
			pie: {
				innerSize: 100,
				depth: 45,
				dataLabels: {
					enabled: true,
					format: '{point.name}: {y}'
				}
			}
		},
		series: [{
			type: 'pie',
			name: 'Region',
			data: ${JSON.stringify(data.data)},
		}],
		credits: {
			enabled: false 
		}
	});
	</script>
    `
}

function project_status_(data) {
	
    return `
    <script>

	Highcharts.chart('project_status', {
		chart: {
			type: 'column'
		},
		title: {
			text: 'Project Status'
		},
		subtitle: {
			text: null
		},
		xAxis: {
			categories: ['Project Status'],
			crosshair: true,
			accessibility: {
				description: 'Countries'
			}
		},
		yAxis: {
			min: 0,
			title: {
				text: null
			}
		},		
		plotOptions: {
			column: {
				pointPadding: 0.2,
				borderWidth: 0
			}
		},
		series: [
			{
				name: 'In Progress',
				data: [${JSON.stringify(data.in_progress)}]
			},
			{
				name: 'Completed',
				data: [${JSON.stringify(data.completed)}]
			},
			{
				name: 'Delayed',
				data: [${JSON.stringify(data.delayed)}]
			}
		]
	});
	</script>
    `
}

function approved_vs_unapproved_projects_(data) {
	
    return `
    <script>

	Highcharts.chart('approved_vs_unapproved_projects', {
		chart: {
			type: 'column'
		},
		title: {
			text: 'Approved VS Unapproved Projects'
		},
		subtitle: {
			text: null
		},
		xAxis: {
			categories: ['Project'],
			crosshair: true,
			accessibility: {
				description: 'Countries'
			}
		},
		yAxis: {
			min: 0,
			title: {
				text: null
			}
		},		
		plotOptions: {
			column: {
				pointPadding: 0.2,
				borderWidth: 0
			}
		},
		series: [
			{
				name: 'Pending',
				data: [${JSON.stringify(data.pending)}]
			},
			{
				name: 'Verified By Project Manager',
				data: [${JSON.stringify(data.approved_by_pm)}]
			},
			{
				name: 'Approved By CEO',
				data: [${JSON.stringify(data.approved_by_ceo)}]
			}
		]
	});
	</script>
    `
}
