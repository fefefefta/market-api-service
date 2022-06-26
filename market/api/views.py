from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import (import_category, import_offer, get_updated_offers,
                       get_statistic, delete_unit_by_id, show_unit_by_id, 
                       validate)
from .models import Import


@transaction.atomic
@api_view(["POST"])
def import_units(request):
    items = request.data["items"]
    update_date = request.data["updateDate"]

    import_ = Import.create_new_import(update_date)

    for item in items:
        # validate(item, items)
        if item.get("type") == "CATEGORY":
            import_category(item, import_)
        else:
            import_offer(item, import_)

    message = {"message": "Вставка или обновление прошли успешно."}
    return Response(message, status=200)


@api_view(["GET"])
def show_unit(request, obj_id):
    response = show_unit_by_id(obj_id)
    return Response(response, status=200)


@transaction.atomic
@api_view(["DELETE"])
def delete_unit(request, obj_id):
    delete_unit_by_id(obj_id)

    response = {"message": "Удаление прошло успешно."}
    return Response(response, status=200)


@api_view(["GET"])
def sales(request):
    date = request.GET.get("date")

    response = get_updated_offers(date)
    return Response(response, status=200)


@api_view(["GET"])
def statistic(request, obj_id):
    date_start = request.GET.get("dateStart")
    date_end = request.GET.get("dateEnd")

    response = get_statistic(obj_id, date_start, date_end)
    return Response(response, status=200)