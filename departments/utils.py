from .models import Department


def get_department_category_map():
    mapping = {}

    departments = Department.objects.filter(
        is_active=True
    ).prefetch_related('categories')

    for department in departments:

        mapping[department.name] = list(
            department.categories.filter(
                is_active=True
            ).order_by('name').values_list('name', flat=True)
        )

    return mapping