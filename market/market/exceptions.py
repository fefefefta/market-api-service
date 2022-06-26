from rest_framework.exceptions import APIException 
from rest_framework.views import exception_handler

class ValidationFailed(APIException):
    status_code = 400
    default_detail = "Validation Failed"
    default_code = "validation_failed"
    detail = {
        "code": status_code,
        "message": default_detail
    }


class ItemNotFound(APIException):
    status_code = 404
    default_detail = "Item not found"
    default_code = "item_not_found"


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, (ValidationFailed, ItemNotFound)):
            response.data["code"] = exc.status_code
            response.data["message"] = exc.default_detail
            del response.data["detail"]
        else:
            response.data["code"] = ValidationFailed.status_code
            response.data["message"] = ValidationFailed.default_detail
            del response.data["detail"]

    return response