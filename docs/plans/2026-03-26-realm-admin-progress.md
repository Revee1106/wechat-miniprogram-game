# Realm Admin Progress

## Completed

- Added `config/realms/realms.json` as the runtime source of truth for realms.
- Added realm config repository and validation services.
- Switched runtime realm loading, breakthrough checks, and event realm filtering to the JSON-backed realm registry.
- Added `/admin/api/realms` CRUD, validation, reload, and reorder endpoints.
- Added admin console realm library and realm editor pages.
- Added automatic runtime reload after realm save, delete, and reorder actions.
- Added delete/disable protection when a realm is still referenced by events.

## Behavior

- Realms are modeled as ordered nodes, so breakthrough now follows the next enabled realm in `order_index`.
- Admin console users can create, edit, delete, and sort realms without editing source code.
- Realm keys remain immutable after creation.
- Reorder operations update `order_index` and immediately reload runtime state.

## Verification

- `C:\\Users\\WANGWENJIE10\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe -m pytest tests/backend -q`
- `C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command "npm.cmd test"`
- `C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command "npm.cmd run build"`
