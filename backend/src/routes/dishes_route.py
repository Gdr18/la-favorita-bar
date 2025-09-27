from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt

from src.models.dish_model import DishModel
from src.utils.json_responses import success_json_response, db_json_response
from src.utils.exception_handlers import ValueCustomError

DISHES_RESOURCE = "plato"

dishes_route = Blueprint("dishes", __name__)


@dishes_route.route("/", methods=["POST"])
@jwt_required()
def add_dish():
    token_role = get_jwt().get("role")
    if token_role != 1:
        raise ValueCustomError("not_auth")
    dish_data = request.get_json()
    if dish_data.get("created_at"):
        raise ValueCustomError("not_auth_set", "created_at")
    dish_object = DishModel(**dish_data)
    dish_object.insert_dish()
    return success_json_response(DISHES_RESOURCE, "añadido", 201)


@dishes_route.route("/")
def get_dishes():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per-page", 10))
    skip = (page - 1) * per_page
    dishes = DishModel.get_dishes(skip, per_page)
    return db_json_response(dishes)


@dishes_route.route("/category/<category>")
def get_category_dishes(category):
    dishes_by_category = DishModel.get_dishes_by_category(category)
    if not dishes_by_category:
        raise ValueCustomError("not_found", DISHES_RESOURCE)
    return db_json_response(dishes_by_category)


@dishes_route.route("/<dish_id>")
def get_dish(dish_id):
    dish = DishModel.get_dish(dish_id)
    if not dish:
        raise ValueCustomError("not_found", DISHES_RESOURCE)
    return db_json_response(dish)


@dishes_route.route("/<dish_id>", methods=["PUT", "DELETE"])
@jwt_required()
def handle_dish(dish_id):
    token_role = get_jwt().get("role")
    if token_role != 1:
        raise ValueCustomError("not_auth")

    if request.method == "PUT":
        dish = DishModel.get_dish(dish_id)
        if not dish:
            raise ValueCustomError("not_found", DISHES_RESOURCE)
        dish_data = request.get_json()
        if dish_data.get("created_at") and dish_data["created_at"] != dish.get(
            "created_at"
        ):
            raise ValueCustomError("not_auth_set", "created_at")
        mixed_data = {**dish, **dish_data}
        dish_object = DishModel(**mixed_data)
        updated_dish = dish_object.update_dish(dish_id)
        return db_json_response(updated_dish)

    if request.method == "DELETE":
        deleted_dish = DishModel.delete_dish(dish_id)
        if not deleted_dish.deleted_count > 0:
            raise ValueCustomError("not_found", DISHES_RESOURCE)
        return success_json_response(DISHES_RESOURCE, "eliminado")
