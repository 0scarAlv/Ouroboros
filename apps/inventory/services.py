from .models import Category


class CategoryService:

    @staticmethod
    def get_all():
        return Category.objects.filter(deleted_at__isnull=True).order_by('name')

    @staticmethod
    def get_by_id(pk):
        return Category.objects.get(pk=pk, deleted_at__isnull=True)

    @staticmethod
    def create(data, user):
        category = Category(**data)
        category.created_by = user
        category.save()
        return category

    @staticmethod
    def update(instance, data, user):
        for field, value in data.items():
            setattr(instance, field, value)
        instance.updated_by = user
        instance.save()
        return instance

    @staticmethod
    def delete(instance, user):
        instance.deleted_by = user
        instance.soft_delete()