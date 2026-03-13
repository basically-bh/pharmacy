app_name = "pharmacy"
app_title = "Pharmacy"
app_publisher = "Basically"
app_description = "ERPNext backend layer for Basically Pharmacy"
app_email = ""
app_license = "mit"

app_version = "0.4.0"

required_apps = ["erpnext"]

# Keep standard ERPNext customizations managed from code so they remain
# reproducible across local, staging, and production environments.
after_install = "pharmacy.setup.setup"
after_migrate = "pharmacy.setup.setup"

auth_hooks = [
	"pharmacy.auth_hooks.validate_mobile_bearer_auth",
]
