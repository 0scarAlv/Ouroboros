from django.db.models import Prefetch

from kernel.models.menu_item import MenuItem


def sidebar_menu(request):
    """
    Injects the sidebar menu into every template context.
    Only includes items the current user is allowed to see. A section
    without its own link is hidden when none of its children are visible.
    """
    if not request.user.is_authenticated:
        return {"sidebar_menu": []}

    active_children = (
        MenuItem.objects
        .filter(is_active=True)
        .select_related("permission__content_type")
    )
    parents = (
        MenuItem.objects
        .filter(is_active=True, parent=None)
        .select_related("permission__content_type")
        .prefetch_related(Prefetch("children", queryset=active_children))
    )

    menu = []
    for parent in parents:
        if not parent.is_accessible_by(request.user):
            continue

        children = [
            child for child in parent.children.all()
            if child.is_accessible_by(request.user)
        ]
        if not children and not parent.url_name:
            continue

        menu.append({
            "item": parent,
            "children": children,
        })

    return {"sidebar_menu": menu}
