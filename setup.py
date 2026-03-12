from setuptools import find_packages, setup

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n") if f.readable() else []

from pharmacy import __version__ as version

setup(
	name="pharmacy",
	version=version,
	description="Pharmacy app for Basically on Frappe/ERPNext",
	author="Basically",
	author_email="info@basically.app",
	packages=find_packages(include=["pharmacy", "pharmacy.*"]),
	zip_safe=False,
	include_package_data=True,
	install_requires=[req for req in install_requires if req],
)
