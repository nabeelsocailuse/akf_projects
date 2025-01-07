// let filters = {};
// frappe.pages['project-survey-dashboard'].on_page_load = async function(wrapper) {
// 	var page = frappe.ui.make_app_page({
// 		parent: wrapper,
// 		title: 'Project Survey Dashboard',
// 		single_column: true
// 	});
// 	await filters.add(page);
// }


frappe.pages['project-survey-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Project Survey Dashboard',
        single_column: true
    });

    server_call.fetch_data(page);
};


server_call = {
    fetch_data: function(page) {
        frappe.call({
            method: "akf_projects.akf_projects.page.project_survey_dashboard.project_survey_dashboard.get_information",
            args: {},
            callback: function(r) {
				
                var info = r.message;
                console.log(info);

                // Render new content
                // $(frappe.render_template("project_survey_dashboard", {
                //     'region_wise_survey': info['region_wise_survey'],
                // })).appendTo(page.main);
				$(frappe.render_template("project_survey_dashboard", r.message)).appendTo(page.main);

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
      _highcharts_.allocated_vs_unallocated_survey(info.allocated_vs_unallocated_survey);     
      _highcharts_.approved_vs_unapproved_survey(info.approved_vs_unapproved_survey);     
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

    allocated_vs_unallocated_survey: function (data) {
        let chart_js = allocated_vs_unallocated_survey_(data)
        $("#allocated_vs_unallocated_survey").html(chart_js)
    }, 

    approved_vs_unapproved_survey: function (data) {
        let chart_js = approved_vs_unapproved_survey_(data)
        $("#approved_vs_unapproved_survey").html(chart_js)
    }, 
     
};

function region_wise_survey_(data) {
	if (!data.data || data.data.length === 0) {
        return '<div class="no-data-message">No data available</div>';
    }
	
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
			text: 'Region Wise Survey Forms',
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
	if (!data.data || data.data.length === 0) {
        return '<div class="no-data-message">No data available</div>';
    }
	
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
			text: 'District Wise Survey Forms',
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
	if (!data.data || data.data.length === 0) {
        return '<div class="no-data-message">No data available</div>';
    }
	
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
			text: 'Tehsil Wise Survey Forms',
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
	if (!data.data || data.data.length === 0) {
        return '<div class="no-data-message">No data available</div>';
    }
	
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
			text: 'Product Wise Survey Forms',
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

function allocated_vs_unallocated_survey_(data) {
	if (!data || (data.allocated === 0 && data.unallocated === 0)) {
        return '<div class="no-data-message">No data available</div>';
    }
	
    return `
    <script>

	Highcharts.chart('allocated_vs_unallocated_survey', {
		chart: {
			type: 'column'
		},
		title: {
			text: 'Allocated VS Unallocated Survey Forms'
		},
		subtitle: {
			text: null
		},
		xAxis: {
			categories: ['Project Survey Forms'],
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
				name: 'Allocated',
				data: [${JSON.stringify(data.allocated)}]
			},
			{
				name: 'Unallocated',
				data: [${JSON.stringify(data.unallocated)}]
			}
		]
	});
	</script>
    `
}

function approved_vs_unapproved_survey_(data) {
	if (!data || (data.pending === 0 && data.verified === 0 && data.approved === 0)) {
        return '<div class="no-data-message">No data available</div>';
    }
	
    return `
    <script>

	Highcharts.chart('approved_vs_unapproved_survey', {
		chart: {
			type: 'column'
		},
		title: {
			text: 'Approved VS Unapproved Survey Forms'
		},
		subtitle: {
			text: null
		},
		xAxis: {
			categories: ['Project Survey Forms'],
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
				name: 'Verified By Regional',
				data: [${JSON.stringify(data.verified)}]
			},
			{
				name: 'Approved By Head Office',
				data: [${JSON.stringify(data.approved)}]
			}
		]
	});
	</script>
    `
}
