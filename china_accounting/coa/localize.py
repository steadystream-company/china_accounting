import csv
import json
import os

import frappe
from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import (
	unset_existing_data,
	build_forest,
)
from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts
from erpnext.setup.setup_wizard.operations.taxes_setup import from_detailed_data


def import_coa(company):
	"""Import Chinese PRC GAAP chart of accounts for the given company."""
	unset_existing_data(company)
	data = get_chart_data_from_csv()
	frappe.local.flags.ignore_root_company_validation = True
	forest = build_forest(data)
	create_charts(company, custom_chart=forest, from_coa_importer=True)
	set_default_accounts(company)
	set_global_defaults()
	change_field_property()
	setup_tax_templates(company)
	setup_tax_rules(company)
	setup_item_group_accounts(company)
	setup_warehouse_accounts(company)


def get_chart_data_from_csv(as_dict=False):
	file_path = os.path.join(os.path.dirname(__file__), "coa_cn.csv")
	data = []
	with open(file_path) as in_file:
		csv_reader = list(csv.reader(in_file))
		headers = csv_reader[0]
		del csv_reader[0]

		for row in csv_reader:
			if as_dict:
				data.append({frappe.scrub(header): row[index] for index, header in enumerate(headers)})
			else:
				if not row[1]:
					row[1] = row[0]
					row[3] = row[2]
				# v16: build_forest expects 8 columns including account_currency
				if len(row) == 7:
					row.append("")
				data.append(row)
	return data


def set_default_accounts(company):
	file_path = os.path.join(os.path.dirname(__file__), "default_accounts.csv")
	with open(file_path) as in_file:
		data = list(csv.reader(in_file))

	company_doc = frappe.get_doc("Company", company)
	company_name = company_doc.name
	values = {
		d[0]: frappe.db.get_value(
			"Account", {"company": company_name, "account_name": d[1], "is_group": 0}
		)
		for d in data
	}
	company_doc.update(values)
	company_doc.save()
	return values


def set_global_defaults():
	frappe.db.set_value(
		"Global Defaults",
		"Global Defaults",
		{"disable_rounded_total": 1, "disable_in_words": 1},
	)


def change_field_property():
	if frappe.db.get_single_value("System Settings", "setup_complete"):
		return
	file_path = os.path.join(os.path.dirname(__file__), "field_property.csv")
	with open(file_path) as in_file:
		data = list(csv.reader(in_file))
	for doctype, field_name, prop, value in data:
		frappe.get_doc(
			{
				"doctype": "Property Setter",
				"doctype_or_field": "DocField",
				"doc_type": doctype,
				"field_name": field_name,
				"property": prop,
				"value": value,
			}
		).insert(ignore_permissions=1)


def setup_tax_templates(company_name):
	file_path = os.path.join(os.path.dirname(__file__), "tax_template.json")
	with open(file_path) as json_file:
		tax_data = json.load(json_file)
	from_detailed_data(company_name, tax_data)


def setup_tax_rules(company_name):
	try:
		abbr = frappe.db.get_value("Company", company_name, "abbr")
		file_path = os.path.join(os.path.dirname(__file__), "tax_rule.csv")
		with open(file_path) as in_file:
			data = list(csv.reader(in_file))
		if data:
			data = data[1:]
		for tax_category, tax_type, tax_template in data:
			template_field = "purchase_tax_template" if tax_type == "Purchase" else "sales_tax_template"
			tax_rule = frappe.get_doc(
				{
					"doctype": "Tax Rule",
					"tax_category": tax_category,
					"tax_type": tax_type,
					template_field: f"{tax_template} - {abbr}",
					"company": company_name,
				}
			)
			tax_rule.insert(ignore_permissions=1)
	except Exception:
		pass


def setup_warehouse_accounts(company):
	abbr = frappe.db.get_value("Company", company, "abbr")
	for wh_detail in [
		("Stores", "1403 - 原材料"),
		("Work In Progress", "141102 - 在用"),
		("Finished Goods", "1405 - 库存商品"),
		("Goods In Transit", "141101 - 在库"),
	]:
		warehouse_name = f"{wh_detail[0]} - {abbr}"
		account_name = f"{wh_detail[1]} - {abbr}"
		frappe.db.set_value("Warehouse", warehouse_name, "account", account_name)


def setup_item_group_accounts(company):
	try:
		abbr = frappe.db.get_value("Company", company, "abbr")
		if frappe.db.exists("Account", f"400101 - 基本生产成本 - {abbr}"):
			for ig_detail in [
				("Consumable", "400101 - 基本生产成本"),
				("Services", "400102 - 辅助生产成本"),
				("Products", "5401 - 主营业务成本"),
			]:
				account_name = f"{ig_detail[1]} - {abbr}"
				if frappe.db.exists("Item Group", ig_detail[0]):
					item_group = frappe.get_doc("Item Group", ig_detail[0])
					item_group.append(
						"item_group_defaults",
						{"company": company, "expense_account": account_name},
					)
					item_group.save()
	except Exception:
		pass
