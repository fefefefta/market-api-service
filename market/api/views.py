from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import (process_category, process_offer, make_representation,
                       get_updated_offers, get_statistic)
from .models import Offer, Category, Import


@transaction.atomic
@api_view(["POST"])
def import_units(request):
    items = request.data["items"]
    update_date = request.data["updateDate"]

    # Проверка даты на соответствие формату
    if True:
        pass

    import_ = Import.objects.create(date=update_date)

    for item in items:
        if item["type"] == "CATEGORY":
            process_category(item, import_)
        else:
            process_offer(item, import_)

    message = {"message": "Вставка или обновление прошли успешно."}
    return Response(message, status=status.HTTP_200_OK)


@api_view(["GET"])
def show_unit(request, obj_id):
    unit = (Category.objects.filter(obj_id=obj_id, is_actual=True)
            or Offer.objects.filter(obj_id=obj_id, is_actual=True)
            .select_related('parent', 'imp'))[0]

    response = make_representation(unit)
    return Response(response, status=status.HTTP_200_OK)


@transaction.atomic
@api_view(["DELETE"])
def delete_unit(request, obj_id):
    unit = (Category.objects.filter(obj_id=obj_id, is_actual=True)
            or Offer.objects.filter(obj_id=obj_id, is_actual=True))[0]
    if isinstance(unit, Category):
        Category.objects.filter(obj_id=obj_id).delete()
    elif isinstance(unit, Offer):
        Offer.objects.filter(obj_id=obj_id).delete()

    message = {"message": "Удаление прошло успешно."}
    return Response(message, status=status.HTTP_200_OK)


@api_view(["GET"])
def sales(request):
    date = request.GET.get("date")
    if True:
        pass

    response = get_updated_offers(date)
    return Response(response, status=status.HTTP_200_OK)


@api_view(["GET"])
def statistic(request, obj_id):
    date_start = request.GET.get("dateStart")
    date_end = request.GET.get("dateEnd")


    response = get_statistic(obj_id, date_start, date_end)
    return Response(response, status=status.HTTP_200_OK)