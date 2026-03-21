from django.core.exceptions import ObjectDoesNotExist


class BaseService:
    """
    Base service class providing common CRUD operations.
    All services in the project should inherit from this class.
    Subclasses must define a 'model' class attribute.
    """

    model = None

    @classmethod
    def get(cls, pk):
        """Retrieve a single record by its primary key. Returns None if not found."""
        try:
            return cls.model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return None

    @classmethod
    def get_all(cls):
        """Retrieve all active (non-deleted) records."""
        return cls.model.objects.filter(deleted_at__isnull=True)

    @classmethod
    def create(cls, data, created_by=None):
        """Create and persist a new record. Optionally assigns created_by."""
        instance = cls.model(**data)
        if created_by:
            instance.created_by = created_by
        instance.save()
        return instance