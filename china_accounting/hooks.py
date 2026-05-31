from . import __version__ as app_version

app_name = "china_accounting"
app_title = "中国会计"
app_publisher = "Steady Stream"
app_description = "中国会计科目表与增值税"
app_email = "info@steadystream.cn"
app_license = "mit"

# Apps
required_apps = ["erpnext"]

# Installation
after_install = "china_accounting.install.after_install"

# Override whitelisted methods
override_whitelisted_methods = {
	"erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country": "china_accounting.overrides.chart_of_accounts.get_charts_for_country",
}

# Override DocType class
override_doctype_class = {
	"Company": "china_accounting.overrides.company.CustomCompany",
}

# Document Events
doc_events = {
	"Company": {
		"validate": "china_accounting.overrides.company.company_validate"
	}
}
