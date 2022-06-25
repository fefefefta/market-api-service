import copy
import datetime
from math import floor

from dateutil import parser
from django.db import IntegrityError

from .models import Offer, Category


def process_category(category_json, import_):
    category_id = category_json["id"]
    parent_id = category_json["parentId"]

    # create parent (if parent is new category but not processed yet)
    if not Category.objects.filter(obj_id=parent_id):
        _create_category(parent_id, import_=import_)

    if Category.objects.filter(obj_id=category_id):
        _process_old_category(category_json, import_)
    else:
        _process_new_category(category_json, import_)


def _process_new_category(category_json, import_):
    ancestors = _get_ancestors(category_json["parentId"])
    try:
        parent = ancestors[0]
    except IndexError:
        parent = None

    _create_category(
            category_json["id"],
            name=category_json["name"],
            all_offers=0,
            offers_price=0,
            parent=parent,
            import_=import_,
            is_actual=True,
        )

    _update_ancestors(
            ancestors, 
            offers_diff=0, 
            price_diff=0, 
            import_=import_
        )


def _process_old_category(category_json, import_):
    category = Category.objects.filter(
            obj_id=category_json["id"],
            is_actual=True
        ).select_related('parent')[0]

    if category.imp != import_:
        _create_history_version(category)

        if category.parent.id == category_json["parentId"]:
            category.name = category_json["name"] or category.name
            category.imp = import_

            ancestors = _get_ancestors(category.parent.obj_id)
            _update_ancestors(ancestors, import_=import_)
        else:
            category.name = category_json["name"] or category.name
            category.imp = import_

            old_ancestors = _get_ancestors(category.parent.obj_id)
            _update_ancestors(
                    old_ancestors, 
                    offers_diff=-category.all_offers,
                    price_diff=-category.offers_price,
                )

            new_ancestors = _get_ancestors(category_json["parentId"])

            try:
                parent = new_ancestors[0]
            except IndexError:
                parent = None

            category.parent = parent
            category.save()

            _update_ancestors(
                    new_ancestors,
                    offers_diff=category.all_offers,
                    price_diff=category.offers_price,
                    import_=import_
                )

    else:
        category.name = category_json["name"] or category.name

        if category.parent.id != category_json["parentId"]:
            old_ancestors = _get_ancestors(category.parent.obj_id)
            _update_ancestors(
                    old_ancestors, 
                    offers_diff=-category.all_offers,
                    price_diff=-category.offers_price,
                )

            try:
                category.parent = Category.objects.filter(
                        obj_id=category_json["parentId"], 
                        is_actual=True
                    )[0]
            except IndexError:
                category.parent = None
            category.save()        

        ancestors = _get_ancestors(category.parent.obj_id)
        _update_ancestors(_update_ancestors(
                    new_ancestors,
                    offers_diff=category.all_offers,
                    price_diff=category.offers_price,
                    import_=import_
                ))


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


def _create_category(
            obj_id,
            parent=None,
            name='', 
            import_=None, 
            all_offers=0, 
            offers_price=0,
            is_actual=True,
        ):
    try:
        category = Category.objects.create(
                obj_id=obj_id,
                name=name,
                all_offers=all_offers,
                offers_price=offers_price,
                parent=parent,
                imp=import_,
                is_actual=True,
            )
    except IntegrityError:
        return None

    return category


def _update_ancestors(ancestors_list, offers_diff=0, 
                      price_diff=0, import_=None):
    def update_ancestor(ancestor, offers_diff=0,
                        price_diff=0, import_=None):
        ancestor.imp = import_ or ancestor.imp
        ancestor.all_offers += offers_diff
        ancestor.offers_price += price_diff
        ancestor.save()

    for ancestor in ancestors_list:
        if ancestor.imp != import_:
            history_version = _create_history_version(ancestor)
            update_ancestor(
                    ancestor, 
                    offers_diff=offers_diff, 
                    price_diff=price_diff, 
                    import_=import_
                )
            history_version.save()
        else:
            update_ancestor(
                    ancestor, 
                    offers_diff=offers_diff, 
                    price_diff=price_diff, 
                    import_=import_
                )


def _create_history_version(unit):
    history_version = copy.copy(unit)
    history_version.pk = None
    history_version.is_actual = False
    return history_version


def process_offer(offer_json, import_):
    offer_id = offer_json["id"]
    parent_id = offer_json["parentId"]

    if not Category.objects.filter(obj_id=parent_id):
        _create_category(parent_id, import_=import_)

    if Offer.objects.filter(obj_id=offer_id):
        _process_old_offer(offer_json, import_)
    else:
        _process_new_offer(offer_json, import_)


def _process_new_offer(offer_json, import_):
    ancestors = _get_ancestors(offer_json["parentId"])
    try:
        parent = ancestors[0]
    except IndexError:
        parent = None

    _create_offer(
            offer_json["id"],
            offer_json["price"],            
            offer_json["name"],
            parent=parent,
            import_=import_,
            is_actual=True,
        )

    _update_ancestors(
            ancestors, 
            offers_diff=1, 
            price_diff=offer_json["price"], 
            import_=import_
        )


def _process_old_offer(offer_json, import_):
    offer = Offer.objects.filter(
            obj_id=offer_json["id"],
            is_actual=True
        ).select_related('parent')[0]
    if offer.parent.id == offer_json["parentId"]:
        history_version = _create_history_version(offer)
        offer.price = offer_json["price"]
        offer.name = offer_json["name"]
        offer.imp = import_
        offer.save()
        history_version.save()

        ancestors = _get_ancestors(offer.parent.obj_id)
        _update_ancestors(
                ancestors, 
                offers_diff=0,
                price_diff=offer.price-history_version.price,
                import_=import_,
            )

    else:
        old_ancestors = _get_ancestors(offer.parent.obj_id)
        _update_ancestors(
                old_ancestors, 
                offers_diff=-1,
                price_diff=-offer.price,
                import_=import_,
            )

        history_version = _create_history_version(offer)
        offer.price = offer_json["price"]
        offer.name = offer_json["name"]
        try:
            offer.parent = Category.objects.filter(
                    obj_id=offer_json["parentId"], 
                    is_actual=True
                )[0]
        except IndexError:
            offer.parent = None
        offer.imp = import_
        offer.save()
        history_version.save()

        new_ancestors = _get_ancestors(offer.parent.obj_id if offer.parent else None)
        _update_ancestors(
                new_ancestors, 
                offers_diff=1,
                price_diff=offer.price,
                import_=import_,
            )


def _create_offer(
            obj_id,
            price,
            name,
            parent=None, 
            import_=None,
            is_actual=True,
        ):
    try:
        offer = Offer.objects.create(
                obj_id=obj_id,
                name=name,
                price=price,
                parent=parent,
                imp=import_,
                is_actual=True,
            )
    except IntegrityError:
        return None

    return offer

#####################SHOW_NODE########################

def make_representation(unit):
    try:
        parent_id = unit.parent.obj_id
    except AttributeError:
        parent_id = None
    if isinstance(unit, Offer):
        return {
                "id": unit.obj_id,
                "name": unit.name,
                "date": _to_ISO8601(unit.imp.date),
                "parentId": parent_id,
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
                "parentId": parent_id,
                "type": "CATEGORY",
                "price": unit.price,
                "children": children
            }
    else:
        raise Exception("БУ!!! Я злющая ошибка, не дам вам никакую ноду!"
                        " Вы где-то оплошали, простофили!")



def _to_ISO8601(date):
    return date

################SALES##################

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


######################STATISTIC#######################

def get_statistic(obj_id, date_start, date_end):

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

