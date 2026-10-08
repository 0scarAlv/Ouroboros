"""
Names of the Material Symbols icons vendored in
kernel/static/vendor/material-symbols. The font is a subset: a name missing
from this list renders as plain text. To add one, add it here and run
`python scripts/update_vendor.py` (needs internet).
"""

# Common icons for business apps (navigation, CRUD, inventory, documents).
# Names: https://fonts.google.com/icons
ICON_NAMES = [
    # Navigation and layout
    'apps', 'arrow_back', 'arrow_downward', 'arrow_forward', 'arrow_upward',
    'chevron_left', 'chevron_right', 'close', 'dashboard', 'expand_less',
    'expand_more', 'home', 'menu', 'more_horiz', 'more_vert', 'open_in_new',
    # Actions
    'add', 'add_circle', 'block', 'check', 'content_copy', 'delete', 'done_all',
    'download', 'edit', 'filter_alt', 'filter_list', 'print', 'redo', 'refresh',
    'remove', 'save', 'search', 'sort', 'swap_horiz', 'sync', 'undo', 'upload',
    'visibility', 'visibility_off',
    # Status and feedback
    'cancel', 'check_circle', 'cloud_off', 'error', 'help', 'info',
    'notifications', 'pending', 'schedule', 'warning',
    # People and access
    'account_circle', 'admin_panel_settings', 'badge', 'group', 'key', 'lock',
    'login', 'logout', 'person', 'person_add', 'settings',
    # Contact and places
    'call', 'location_on', 'mail', 'store',
    # Documents and records
    'attach_file', 'backup', 'calendar_month', 'description', 'folder',
    'history', 'picture_as_pdf', 'receipt_long', 'restore', 'table_view',
    # Inventory, sales and money
    'barcode_scanner', 'category', 'factory', 'inventory', 'inventory_2',
    'label', 'local_shipping', 'medication', 'payments', 'point_of_sale',
    'qr_code_scanner', 'shopping_cart', 'warehouse',
    # Reports
    'bar_chart', 'trending_down', 'trending_up',
]

ICON_SET = frozenset(ICON_NAMES)
