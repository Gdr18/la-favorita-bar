from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt
from pymongo.errors import PyMongoError

from src.models.product_model import ProductModel
from src.models.dish_model import DishModel
from src.utils.exception_handlers import ValueCustomError
from src.utils.json_responses import success_json_response, db_json_response
from src.services.db_service import client

PRODUCTS_RESOURCE = "producto"

products_route = Blueprint("products", __name__)


@products_route.route("/", methods=["POST"])
@jwt_required()
def add_product() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if token_role != 1:
        raise ValueCustomError("not_auth")
    product_data = request.get_json()
    if product_data.get("created_at"):
        raise ValueCustomError("not_auth_set", "created_at")
    product_object = ProductModel(**product_data)
    product_object.insert_product()
    return success_json_response(PRODUCTS_RESOURCE, "añadido", 201)


@products_route.route("/", methods=["GET"])
@jwt_required()
def get_products() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not any([token_role == 1, token_role == 2]):
        raise ValueCustomError("not_auth")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per-page", 10))
    skip = (page - 1) * per_page
    products = ProductModel.get_products(skip, per_page)
    return db_json_response(products)


@products_route.route("/<product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id) -> tuple[Response, int]:
    session = client.start_session()
    token_role = get_jwt().get("role")
    if not any([token_role == 1, token_role == 2]):
        raise ValueCustomError("not_auth")
    product = ProductModel.get_product(product_id)
    if not product:
        raise ValueCustomError("not_found", PRODUCTS_RESOURCE)
    new_product_data = request.get_json()
    if new_product_data.get("created_at") and new_product_data[
        "created_at"
    ] != product.get("created_at"):
        raise ValueCustomError("not_auth_set", "created_at")
    combined_data = {**product, **new_product_data}
    product_object = ProductModel(**combined_data)
    try:
        session.start_transaction()
        updated_product = product_object.update_product(product_id, session)
        updated_product_stock = updated_product.get("stock")
        product_stock = product.get("stock")
        if product_stock != updated_product_stock and 0 in (
            updated_product_stock,
            product_stock,
        ):
            DishModel.update_dishes_availability(
                updated_product.get("name"), updated_product_stock != 0, session
            )
        session.commit_transaction()
        return db_json_response(updated_product)
    except Exception as e:
        session.abort_transaction()
        raise e
    finally:
        session.end_session()


@products_route.route("/<product_id>", methods=["GET", "DELETE"])
@jwt_required()
def handle_product(product_id: str) -> tuple[Response, int]:
    token_role = get_jwt().get("role")

    if request.method == "GET":
        if not any([token_role == 1, token_role == 2]):
            raise ValueCustomError("not_auth")
        product = ProductModel.get_product(product_id)
        if product:
            return db_json_response(product)
        else:
            raise ValueCustomError("not_found", PRODUCTS_RESOURCE)

    if request.method == "DELETE":
        if token_role != 1:
            raise ValueCustomError("not_auth")
        deleted_product = ProductModel.delete_product(product_id)
        if deleted_product.deleted_count > 0:
            return success_json_response(PRODUCTS_RESOURCE, "eliminado")
        else:
            raise ValueCustomError("not_found", PRODUCTS_RESOURCE)
