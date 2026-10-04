def can_view(user, attachment):
    """
    A user may see an attachment if they can view attachments and can view
    the record it belongs to (e.g. `parties.view_party`).
    """
    owner = attachment.content_type
    return (
        user.is_active
        and user.has_perm('attachments.view_attachment')
        and user.has_perm(f'{owner.app_label}.view_{owner.model}')
    )
