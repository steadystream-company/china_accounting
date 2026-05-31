import frappe
from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import (
	get_charts_for_country as original_get_charts_for_country,
)


@frappe.whitelist()
def get_charts_for_country(country=None, with_standard=False):
	charts = original_get_charts_for_country(country, with_standard)
	if country in ("中国", "China", "CN"):
		charts.append("中国会计科目表")
	return charts
