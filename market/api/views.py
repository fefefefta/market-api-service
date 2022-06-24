from collections import deque

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import OfferSerializer, CategorySerializer
from .services import process_category, process_offer
from .models import Offer, Category, Import


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
def show_unit(request):
    pass


@api_view(["DELETE"])
def delete_unit(request):
    pass

    # update_date = request.data["updateDate"]
    # items = request.data["items"]
    # changed_categories = {}
    # first_level_categories = []

    # for item in items:
    #     data = item
    #     data["date"] = update_date
    #     price_change = new_offers_sum = 0 

    #     if data["type"] == "CATEGORY":
    #         first_level_categories.append(data["id"])
    #         try:
    #             changed_categories[data["id"]]["price_change"] += 0
    #             changed_categories[data["id"]]["new_offers_sum"] += 0
    #         except KeyError:
    #             changed_categories[data["id"]] = {
    #                 "price_change": price_change, 
    #                 "new_offers_sum": new_offers_sum,
    #                 "name": data["name"],
    #                 "parent_id": data["parentId"],
    #             }
    #         finally:
    #             price_change = changed_categories[data["id"]]["price_change"]
    #             new_offers_sum = changed_categories[data["id"]]["new_offers_sum"]

    #     elif data["type"] == "OFFER":
    #         if data["parentId"] not in first_level_categories:
    #             first_level_categories.append(data["parentId"])
    #         offer_serializer = OfferSerializer(data={
    #                 "name": data["name"],
    #                 "parent_id": data.get("parentId"),
    #                 "obj_id": data["id"],
    #                 "date": data["date"],
    #                 "price": data["price"]
    #             })
    #         if offer_serializer.is_valid():
    #             offer_serializer.save()
    #             price_change, new_offers_sum = (
    #                     offer_serializer.price_change, 
    #                     offer_serializer.new_offers_sum,
    #                 )
    #         print(offer_serializer.errors)

    #     else:
    #         raise Exception('какая-то ошибка, потом придумать, какая')

    #     try:
    #         changed_categories[data["parentId"]]["price_change"] += price_change
    #         changed_categories[data["parentId"]]["new_offers_sum"] += new_offers_sum
    #     except KeyError:
    #         changed_categories[data["parentId"]] = {
    #             "price_change": price_change, 
    #             "new_offers_sum": new_offers_sum,
    #         }

    # categories_queue = deque(first_level_categories)
    # print(categories_queue, first_level_categories)
    # seen_categories = []
    # while categories_queue:
    #     category_id = categories_queue.popleft()
    #     if category_id in seen_categories:
    #         continue
    #     try:
    #         parent_id = Category.objects.get(
    #                 obj_id=category_id,
    #                 is_actual=True
    #             ).parent_id
    #     except Category.DoesNotExist:
    #         seen_categories.append(category_id)
    #         continue

    #     try:
    #         print(changed_categories[category_id]["price_change"])
    #         changed_categories[parent_id]["price_change"] += (
    #                 changed_categories[category_id]["price_change"]
    #             )
    #         changed_categories[parent_id]["new_offers_sum"] += (
    #                 changed_categories[category_id]["new_offers_sum"]
    #             )
    #     except KeyError:
    #         changed_categories[parent_id] = {
    #             "price_change": changed_categories[category_id]["price_change"], 
    #             "new_offers_sum": changed_categories[category_id]["new_offers_sum"],
    #         }

    #     categories_queue.append(parent_id)
    #     seen_categories.append(category_id)

    # print(changed_categories)

    # for category, changes in changed_categories.items():
    #     data = {
    #         "obj_id": category,
    #         "date": update_date,
    #         "price_change": changes["price_change"],
    #         "new_offers_sum": changes["new_offers_sum"],
    #         "name": changes.get("name"),
    #         "parent_id": changes.get("parent_id")
    #     }

    #     category_serializer = CategorySerializer(data=data)
    #     # print('1')
    #     if category_serializer.is_valid():
    #         # print('2')
    #         category_serializer.save()
    #         # print('3')
    #     print(category_serializer.errors)
    #     message = {"message": "Вставка или обновление прошли успешно."}
    # return Response(message, status=status.HTTP_200_OK)





        



