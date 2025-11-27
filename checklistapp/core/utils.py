from django.db.models import F

def reorder_items(queryset, item_id, new_order):
    """Reorder items in a queryset"""
    item = queryset.get(id=item_id)
    old_order = item.order
    
    if new_order < old_order:
        # Moving up
        queryset.filter(
            order__gte=new_order,
            order__lt=old_order
        ).update(order=F('order') + 1)
    else:
        # Moving down
        queryset.filter(
            order__gt=old_order,
            order__lte=new_order
        ).update(order=F('order') - 1)
    
    item.order = new_order
    item.save()