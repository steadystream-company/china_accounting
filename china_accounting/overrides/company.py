import frappe
from erpnext.setup.doctype.company.company import Company
from china_accounting.coa.localize import import_coa


class CustomCompany(Company):
	def create_default_accounts(self):
		if self.chart_of_accounts == "中国会计科目表":
			self.create_default_warehouses()
			frappe.local.flags.ignore_root_company_validation = True
			frappe.local.flags.ignore_chart_of_accounts = True
			import_coa(self.name)
		else:
			super().create_default_accounts()


def company_validate(doc, method):
	"""Hook into Company validation to handle any China-specific logic."""
	pass
