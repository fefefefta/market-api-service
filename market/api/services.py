import datetime

from dateutil import parser
from django.db import IntegrityError

from .models import Offer, Category


########################IMPORT##########################

def import_category(category_json, import_):
    category_id = category_json["id"]
    parent_id = category_json["parentId"]

    # create parent (if parent is new category but not processed yet)
    if (not Category.objects.filter(obj_id=parent_id)
            and parent_id is not None):
        Category.objects.create(
                obj_id=parent_id,
                imp=import_,
                name='',
                offers_price=0,
                all_offers=0,
                is_actual=True,
                parent=None,
            )

    if Category.objects.filter(obj_id=category_id):
        _import_old_category(category_json, import_)
    else:
        _import_new_category(category_json, import_)


def _import_new_category(category_json, import_):
    ancestors = _get_ancestors(category_json["parentId"])
    try:
        parent = ancestors[0]
    except IndexError:
        parent = None

    Category.objects.create(
            obj_id=category_json["id"],
            imp=import_,
            name=category_json["name"],
            offers_price=0,
            all_offers=0,
            is_actual=True,
            parent=parent,
        )

    _update_ancestors(
            ancestors, 
            offers_diff=0, 
            price_diff=0, 
            imp=import_
        )


def _import_old_category(category_json, import_):
    category = Category.objects.filter(
            obj_id=category_json["id"],
            is_actual=True
        ).select_related('parent')[0]

    parent_id = category.parent.obj_id if category.parent else None

    # If current import equals import in json then history version already
    # exists, it was created while updating category as ancestor. Or it is new
    # category and was created as parent. So it doesnt need a history version.
    if category.imp != import_:
        history_version = category.create_history_version()

    category.name = category_json["name"]
    category.imp = import_

    # If parent is not updating for category
    if parent_id == category_json["parentId"]:
        category.save()
        history_version.save()

        ancestors = _get_ancestors(parent_id)
        _update_ancestors(ancestors, imp=import_)
    else:
        try:
            parent = Category.objects.filter(obj_id=category_json["parentId"],
                                             is_actual=True)[0]
        except IndexError:
            if category_json["parentId"] is None:
                parent = None
            else:
                raise Exception("КИНУЛИ НЕРЕАЛЬНОГО РОДИТЕЛЯ")
        category.parent = parent
        category.save()
        history_version.save()

        # If parent is updating for category then we have to subtract
        # category' offers and price from old ancestors and add them to new.
        old_ancestors = _get_ancestors(parent_id)
        _update_ancestors(
                old_ancestors,
                offers_diff=-category.all_offers,
                price_diff=-category.offers_price,
                imp=import_
            )

        new_ancestors = _get_ancestors(category_json["parentId"])
        _update_ancestors(
                new_ancestors,
                offers_diff=category.all_offers,
                price_diff=category.offers_price,
                imp=import_
            )


def _get_ancestors(parent_id):
    """
    Gets the id of parent category, returns a list of ancestral categories 
    in order from the parent to the root.
    """
    if not parent_id:
        return []

    query = """
    WITH RECURSIVE ancestors AS (
        SELECT api_category.*, 0 AS level
        FROM api_category
        WHERE obj_id = %s AND is_actual = TRUE

        UNION ALL

        SELECT api_category.*, level + 1 AS level
        FROM api_category, ancestors
        WHERE api_category.id = ancestors.parent_id
              AND api_category.is_actual = TRUE 
    )
    SELECT *
    FROM ancestors
    ORDER BY level;
    """

    return Category.objects.raw(query, [parent_id])


def _update_ancestors(ancestors_list, offers_diff=0, 
                      price_diff=0, imp=None):
    def update_ancestor(ancestor, offers_diff=0,
                        price_diff=0, imp=None):
        ancestor.imp = imp or ancestor.imp
        ancestor.all_offers += offers_diff
        ancestor.offers_price += price_diff
        ancestor.save()

    for ancestor in ancestors_list:
        if ancestor.imp != imp:
            # history_version = _create_history_version(ancestor)
            history_version = ancestor.create_history_version()
            update_ancestor(
                    ancestor, 
                    offers_diff=offers_diff, 
                    price_diff=price_diff, 
                    imp=imp
                )
            history_version.save()
        else:
            update_ancestor(
                    ancestor, 
                    offers_diff=offers_diff, 
                    price_diff=price_diff, 
                    imp=imp
                )


def import_offer(offer_json, import_):
    offer_id = offer_json["id"]
    parent_id = offer_json["parentId"]

    if not Category.objects.filter(obj_id=parent_id):
        Category.objects.create(
                obj_id=parent_id,
                imp=import_,
                name='',
                offers_price=0,
                all_offers=0,
                is_actual=True,
                parent=None,
            )

    if Offer.objects.filter(obj_id=offer_id):
        _import_old_offer(offer_json, import_)
    else:
        _import_new_offer(offer_json, import_)


def _import_new_offer(offer_json, import_):
    ancestors = _get_ancestors(offer_json["parentId"])
    try:
        parent = ancestors[0]
    except IndexError:
        parent = None

    Offer.objects.create(
            obj_id=offer_json["id"],
            imp=import_,
            name=offer_json["name"],
            price=offer_json["price"],
            is_actual=True,
            parent=parent,
        )

    _update_ancestors(
            ancestors, 
            offers_diff=1, 
            price_diff=offer_json["price"], 
            imp=import_
        )


def _import_old_offer(offer_json, import_):
    offer = Offer.objects.filter(
            obj_id=offer_json["id"],
            is_actual=True
        ).select_related('parent')[0]

    parent_id = offer.parent.obj_id if offer.parent else None

    history_version = offer.create_history_version()

    offer.name = offer_json["name"]
    offer.price = offer_json["price"]
    offer.imp = import_

    if parent_id == offer_json["parentId"]:
        offer.save()
        history_version.save()

        ancestors = _get_ancestors(parent_id)
        _update_ancestors(
                ancestors,
                offers_diff=0,
                price_diff=offer.price-history_version.price,
                imp=import_
            )
    else:
        try:
            parent = Offer.objects.filter(obj_id=offer_json["parentId"],
                                          is_actual=True)[0]
        except IndexError:
            if offer_json["parentId"] is None:
                parent = None
            else:
                raise Exception("КИНУЛИ НЕРЕАЛЬНОГО РОДИТЕЛЯ")
        offer.parent = parent
        offer.save()
        history_version.save()

        old_ancestors = _get_ancestors(parent_id)
        _update_ancestors(
                old_ancestors,
                offers_diff=-1,
                price_diff=-offer.price,
                imp=import_
            )

        new_ancestors = _get_ancestors(offer_json["parentId"])
        _update_ancestors(
                new_ancestors,
                offers_diff=1,
                price_diff=offer.price,
                imp=import_
            )

########################DELETE_UNIT#########################

def delete_unit_by_id(obj_id):
    versions_to_delete = (Category.objects.filter(obj_id=obj_id)
                          or Offer.objects.filter(obj_id=obj_id))
    actual_unit = versions_to_delete.filter(is_actual=True)[0]
    parent_id = (actual_unit.parent.obj_id if actual_unit.parent
                 else None)

    ancestors = _get_ancestors(parent_id)
    if isinstance(actual_unit, Category):
        _update_ancestors(
                ancestors,
                offers_diff=-actual_unit.all_offers,
                price_diff=-actual_unit.offers_price,
                imp=actual_unit.imp
            )
    else:
        _update_ancestors(
                ancestors,
                offers_diff=-1,
                price_diff=-actual_unit.price,
                imp=actual_unit.imp
            )

    versions_to_delete.delete()

########################SHOW_UNIT#########################

def make_representation(unit):

    if isinstance(unit, Offer):
        return {
                "id": unit.obj_id,
                "name": unit.name,
                "date": _to_ISO8601(unit.imp.date),
                "parentId": unit.parent.obj_id if unit.parent else None,
                "type": "OFFER",
                "price": unit.price,
                "children": None
            }
    elif isinstance(unit, Category):
        children_offers = unit.children_offers.filter(is_actual=True)
        children_categories = unit.children_categories.filter(is_actual=True)

        children = (list(map(make_representation, children_offers))
                    + list(map(make_representation, children_categories)))
        return {
                "id": unit.obj_id,
                "name": unit.name,
                "date": _to_ISO8601(unit.imp.date),
                "parentId": unit.parent.obj_id if unit.parent else None,
                "type": "CATEGORY",
                "price": unit.price,
                "children": children
            }
    else:
        raise Exception("БУ!!! Я злющая ошибка, не дам вам никакую ноду!"
                        " Вы где-то оплошали, простофили!")


def _to_ISO8601(date):
    return date

########################SALES#########################

def get_updated_offers(date):
    finish_date = parser.isoparse(date)
    start_date = finish_date - datetime.timedelta(days=1)

    updated_offers = Offer.objects.filter(
            imp__date__gte=start_date,
            imp__date__lte=finish_date
        ).select_related('imp', 'parent')

    response = []
    for offer in updated_offers:
        offer_dict = {
            "id": offer.obj_id,
            "name": offer.name,
            "parentId": offer.parent.obj_id if offer.parent else None,
            "type": "OFFER",
            "price": offer.price,
            "date": _to_ISO8601(offer.imp.date)
        }
        response.append(offer_dict)

    return response

########################STATISTIC##########################

def get_statistic(obj_id, date_start, date_end):
    # To find out unit's type
    test_version = (Category.objects.filter(obj_id=obj_id)
                    or Offer.objects.filter(obj_id=obj_id))[0]
    if isinstance(test_version, Category):
        versions = Category.objects.filter(
                obj_id=obj_id,
            ).select_related('imp', 'parent')
        type_ = "CATEGORY"
    elif isinstance(test_version, Offer):
        versions = Category.objects.filter(
                obj_id=obj_id,
            ).select_related('imp', 'parent')
        type_ = "OFFER"

    if date_start:
        versions.filter(imp__date__gte=date_start)
    if date_end:
        versions.filter(imp__date__lt=date_end)

    response = []
    for version in versions:
        version_dict = {
            "id": version.obj_id,
            "name": version.name,
            "parentId": version.parent.obj_id if version.parent else None,
            "type": type_,
            "price": version.price,
            "date": _to_ISO8601(version.imp.date)
        }
        response.append(version_dict)

    return response
