# Pharmacy App Structure Plan

## Current state

The app already follows the standard Frappe outer/inner layout:

- `pharmacy/` is the app repository root.
- `pharmacy/pharmacy/` is the default module package that contains DocTypes and workspaces.

The current inconsistency is that application code is split across two levels:

- Root package code: `pharmacy/api`, `pharmacy/services`, `pharmacy/setup`, `pharmacy/utils`
- Module package code: `pharmacy/pharmacy/doctype`, `pharmacy/pharmacy/workspace`

## Safe target

For a non-breaking ERPNext-aligned structure, keep:

- `pharmacy/hooks.py`
- `pharmacy/modules.txt`
- `pharmacy/patches.txt`
- `pharmacy/public/`
- `pharmacy/templates/`
- `pharmacy/www/` when needed
- `pharmacy/api/`
- `pharmacy/setup/`
- `pharmacy/utils/`
- `pharmacy/pharmacy/doctype/`
- `pharmacy/pharmacy/workspace/`

## Why this is the safe target

These import and runtime entry points are already active:

- `pharmacy.setup.setup`
- `pharmacy.api.mobile.*`
- `pharmacy.services.*`
- `pharmacy.utils.*`

Moving those packages into `pharmacy/pharmacy/` without compatibility shims would break:

- hook entry points in `hooks.py`
- whitelisted API method paths used by clients and `bench execute`
- internal imports across services and API handlers

## Next refactor phases

1. Clean generated files and ignore them in Git.
2. Keep public/runtime paths stable.
3. If package moves are still desired, introduce compatibility shims first.
4. Migrate imports in small batches and verify each batch inside Docker/bench.
