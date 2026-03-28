from core.models.menu_item import MenuItem


def sidebar_menu(request):
    """
    Injects the sidebar menu into every template context.
    Only includes items the current user is allowed to see.
    """
    if not request.user.is_authenticated:
        return {"sidebar_menu": []}

    parents = (
        MenuItem.objects
        .filter(is_active=True, parent=None)
        .prefetch_related("children", "groups", "children__groups")
    )

    menu = []
    for parent in parents:
        if not parent.is_accessible_by(request.user):
            continue

        children = [
            child for child in parent.children.filter(is_active=True)
            if child.is_accessible_by(request.user)
        ]

        menu.append({
            "item": parent,
            "children": children,
        })

    return {"sidebar_menu": menu}