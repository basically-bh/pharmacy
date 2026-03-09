# Copyright (c) 2026, Basically and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from pharmacy.utils.customer_profile import validate_customer_matches_profile


class AppOrder(Document):
	"""Mobile-app orchestration document ahead of ERP sales documents."""

	def validate(self) -> None:
		validate_customer_matches_profile(self)
