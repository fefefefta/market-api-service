import datetime
import uuid

from dateutil import parser
from django.db import IntegrityError

from market.exceptions import ItemNotFound, ValidationFailed
from .models import Offer, Category


########################IMPORT##########################

def validate(unit_json, units):
    # validate id
    try:
        uuid.UUID(unit_json["id"])
    except ValueError:
        raise ValidationFailed

    # validate parentId
    try:
        uuid.UUID(unit_json["parentId"])
    except ValueError:
        if unit_json["parentId"] is not None:
            raise ValidationFailed

    # validate parentId does not exist
    if (unit_json["parentId"] is not None
            and not Category.objects.filter(obj_id=unit_json["parentId"])
            and unit_json["parentId"] not in [unit["id"] for unit in units]):
        raise ValidationFailed

    # validate name
    if unit_json["name"] == '' or unit_json["name"] is None:
        raise ValidationFailed

    # validate type
    if unit_json["type"] != any("OFFER", "CATEGORY"):
        raise ValidationFailed

    # validate price
    if (unit_json["type"] == "OFFER"
            and not isinstance(unit_json["price"], int)):
        raise ValidationFailed
    elif isinstance(unit_json["price"], int) and unit_json["price"] < 0:
        raise ValidationFailed

    elif unit_json["type"] == "CATEGORY" and unit_json["price"] is None:
        raise ValidationFailed

    # check type have not changed
    if (unit_json["type"] == "OFFER" 
            and Category.objects.filter(obj_id=unit_json["id"])):
        raise ValidationFailed
    elif (unit_json["type"] == "CATEGORY" 
            and Offer.objects.filter(obj_id=unit_json["id"])):
        raise ValidationFailed


def import_category(category_json, import_):
    """
    Creates a parent if it is also a new category, but has not been
    processed yet. Then imports the units.
    """
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
    """Creates a new category and updates the date in the ancestors"""
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
    """
    Copies the current state of the category and creates a historical
    version for statistics. Then updates the state of the category and the
    date of the ancestors. If the parent of a category changes, then the offers
    and the total price are deducted from the old ancestors in order to add
    them to the new ancestors.
    """
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
    """
    Updates the ancestors of the updated unit. If the current version of the
    ancestor refers to an old import, then a historical version of the ancestor
    is created, and the import of the current ancestor is updated.
    """
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
    """Same as in the import_category"""
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
    """Same as in the _import_new_category"""
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
    """Same as in the _import_old_category"""
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
    """
    Finds the unit and updates the ancestors, subtracting the cost of deleted
    offers from them.
    """
    versions_to_delete = (Category.objects.filter(obj_id=obj_id)
                          or Offer.objects.filter(obj_id=obj_id))
    try:
        actual_unit = versions_to_delete.filter(is_actual=True)[0]
    except IndexError:
        raise ItemNotFound

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

def show_unit_by_id(obj_id):
    """Finds the unit and make its representation"""
    try:
        unit = (Category.objects.filter(obj_id=obj_id, is_actual=True)
                or Offer.objects.filter(obj_id=obj_id, is_actual=True)
                .select_related('parent', 'imp'))[0]
    except IndexError:
        raise ItemNotFound

    return _make_representation(unit)

def _make_representation(unit):
    """Creates a hierarchical json representation of an object."""
    if isinstance(unit, Offer):
        return {
                "id": unit.obj_id,
                "name": unit.name,
                "date": unit.imp.date,
                "parentId": unit.parent.obj_id if unit.parent else None,
                "type": "OFFER",
                "price": unit.price,
                "children": None
            }
    else:
        children_offers = unit.children_offers.filter(is_actual=True)
        children_categories = unit.children_categories.filter(is_actual=True)

        children = (list(map(_make_representation, children_offers))
                    + list(map(_make_representation, children_categories)))
        return {
                "id": unit.obj_id,
                "name": unit.name,
                "date": unit.imp.date,
                "parentId": unit.parent.obj_id if unit.parent else None,
                "type": "CATEGORY",
                "price": unit.price,
                "children": children
            }

########################SALES#########################

def get_updated_offers(date):
    """
    Validates the date and returns all versions of objects created in the
    segment [date - 24h, date]
    """
    try:
        finish_date = parser.isoparse(date)
    except (ValueError, parser.ParserError):
        raise ValidationFailed
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
            "date": offer.imp.date
        }
        response.append(offer_dict)

    return response

########################STATISTIC##########################

def get_statistic(obj_id, date_start, date_end):
    """
    Validates dates and returns a list of versions of object with obj_id=obj_id
    created in the interval [date_start, date_end)
    """
    versions = ((Category.objects.filter(obj_id=obj_id)
                 or Offer.objects.filter(obj_id=obj_id))
                .select_related('imp', 'parent'))
    if len(versions) == 0:    
        raise ItemNotFound

    if isinstance(versions[0], Category):
        type_ = "CATEGORY"
    elif isinstance(versions[0], Offer):
        type_ = "OFFER"

    if date_start:
        try:
            date_start = parser.isoparse(date_start)
        except (ValueError, parser.ParserError):
            raise ValidationFailed
        versions = versions.filter(imp__date__gte=date_start)
    if date_end:
        try:
            date_end = parser.isoparse(date_end)
        except (ValueError, parser.ParserError):
            raise ValidationFailed
        versions = versions.filter(imp__date__lt=date_end)

    response = []
    for version in versions:
        version_dict = {
            "id": version.obj_id,
            "name": version.name,
            "parentId": version.parent.obj_id if version.parent else None,
            "type": type_,
            "price": version.price,
            "date": version.imp.date
        }
        response.append(version_dict)

    return response
