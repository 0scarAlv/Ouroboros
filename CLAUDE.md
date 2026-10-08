# Ouroboros — project conventions

Ouroboros is a reusable Django 5.2 base. Client products (each its own
deployment, one instance per client, no multi-tenancy) start from it and
add their own domain modules. Keep the base generic: nothing
industry-specific (pharma, manufacturing, …) belongs here.

## Layers and what goes where

| Layer | Folder | Rule |
|---|---|---|
| Kernel | `kernel/`, `apps/authentication/` | Everything every product needs unchanged: audit models, CRUD views, menu, security, settings profiles. |
| Optional module | `apps/<module>/` listed in `MODULE_APPS` | Needed by some products (`parties`, `attachments`). Built only when a real project asks for it. |
| Product | the product's own repo | Everything else (domain models, reports, integrations). |

- Modules depend on the kernel only, **never on each other**. Cross-module
  links go through generic relations (see `attachments`) or live in the
  product.
- The base grows by extracting what real products already built, not by
  guessing.

## Models: pick an audit level

Every model inherits one of the kernel bases (`kernel.models`), all with a
UUID primary key:

| Level | Base | Adds | Use for |
|---|---|---|---|
| 0 | `BaseModel` | `created_at`, `updated_at` | High-volume or technical tables |
| 1 | `AuditModel` | who created/changed, soft delete (`objects` hides deleted, `all_objects` keeps them) | Default for business records |
| 2 | `TrackedModel` | full change history (`instance.history`) | Records that must be traceable (regulated data) |

The acting user is filled from the request by `CurrentUserMiddleware`;
outside a request (commands, tasks, tests) wrap writes in
`kernel.current_user.acting_as(user)`.

## Creating a module

```bash
python manage.py startmodule products --model Product --audit 1
```

This renders `kernel/scaffold/module/` (the reference module) into
`apps/products/`; follow the printed next steps (register the app, include
its URLs, migrate, add a menu item in the admin). Keep generated modules
in that shape:

```
apps/<module>/
  apps.py        # name='apps.<module>', label='<module>'
  models.py      # on a kernel base model
  forms.py       # kernel.utils.forms.BaseModelForm
  views.py       # subclasses of kernel.views.Crud*View
  urls.py        # app_name = '<module>'
  admin.py       # SimpleHistoryAdmin for TrackedModel
  factories.py   # factory_boy factories for every model
  tests/         # pytest functions
```

When the scaffold changes, `kernel/tests/test_startmodule.py` must keep
passing: it generates a module per audit level and runs its tests.

## Views, URLs and permissions

- Use the kernel CRUD views (`CrudListView`, `CrudDetailView`,
  `CrudCreateView`, `CrudUpdateView`, `CrudDeleteView`, `CrudHistoryView`).
  They require the model permission (`view`/`add`/`change`/`delete`) and
  log 403s as security events. A custom view must check permissions too
  (`PermissionRequiredMixin`); never rely on hiding a link.
- URL names: `<app_label>:<model_name>_<action>` (`list` is required;
  `detail`, `create`, `update`, `delete`, `history` are optional and the
  templates only offer the ones that exist).
- Override a CRUD template per model with
  `templates/<app_label>/<model_name>_<list|detail|form|confirm_delete|history>.html`.
- The list page has one toolbar (Nuevo, Modificar, Eliminar, Historial, Ver)
  acting on the selected row; detail, forms, delete and history open via
  htmx in a panel above the table (`kernel/static/js/crud.js`). An htmx
  request to those views returns only the partial
  `crud/_<detail|form|confirm_delete|history>.html`, overridable with
  `templates/<app_label>/_<model_name>_<suffix>.html`; the full pages
  include the same partial. A successful change from the panel answers 204
  with `HX-Trigger` (`showToast`, `crudChanged`) instead of a redirect.
- Access is given with groups holding Django permissions. The sidebar menu
  (`kernel.MenuItem`) is configured per install in the admin; each item
  points to one permission.

## Front end

- Server-rendered Django templates, Bootstrap 5, htmx and Alpine, all
  vendored under `kernel/static/vendor/` (the app must work offline;
  update with `scripts/update_vendor.py`). No CDNs.
- The CSP forbids inline scripts: put JavaScript in static files.
- UI text is Spanish; form errors use the codes in
  `kernel.utils.forms.DEFAULT_ERROR_CODES`, translated by
  `kernel/constants/general.py`.

## Security baseline (do not weaken)

Argon2 passwords, django-axes lockout by username, fixed 8-hour sessions,
`SecurityEvent` append-only log (logins, failures, lockouts, 403s, file
downloads), CSP and security headers. Files are served only through
permission-checked views (`attachments`), never from `MEDIA_URL`.

## Tests

- pytest is the runner (`pytest`, `pytest apps/<module>`, `pytest --cov`,
  `pytest -m "not slow"` to skip the scaffold test).
- Plain pytest functions, data from `factories.py`
  (`UserFactory(permissions=['app.view_model'])` for access tests).
- Every module tests its permissions (403 without them) and its audit
  behaviour.

## Settings

`config.settings.dev` (default for `manage.py`), `prod` (server with
HTTPS), `onprem` (client PC on its LAN: waitress via `manage.py serve`,
WhiteNoise, data under `DATA_DIR`). One `DATABASE_URL` selects the
database (SQLite by default, Postgres supported).

## Language

Code, comments, docstrings, commit messages and issues in English; UI text
in Spanish.
