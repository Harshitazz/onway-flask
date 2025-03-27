from flask import Blueprint, request, jsonify
from db import db

# Convert MongoDB document to JSON-friendly format
def serialize_cart(cart):
    return {
        "_id": str(cart["_id"]),
        "user_id": cart["user_id"],
        "items": [
            {
                "uniq_id": item["uniq_id"],
                "product_name": item["product_name"],
                "quantity": int(item["quantity"]),
                "discounted_price": item["discounted_price"],
                "image": item["image"]
            } for item in cart["items"]
        ],
        "total_price": cart["total_price"]
    }


cart_blueprint = Blueprint("cart", __name__)

carts_collection = db["carts"]

# Get user cart
@cart_blueprint.route('/<user_id>', methods=['GET'])
def get_cart(user_id):
    cart = carts_collection.find_one({"user_id": user_id})
    if cart:
        return jsonify(serialize_cart(cart))
    return jsonify({"message": "Cart is empty", "items": [], "total_price": 0}), 200

# Add item to cart
@cart_blueprint.route('/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data["user_id"]
    product = data["product"]

    # Ensure quantity & price are integers
    product["quantity"] = int(product["quantity"])
    product["discounted_price"] = int(product["discounted_price"])

    cart = carts_collection.find_one({"user_id": user_id})

    if cart:
        items = cart["items"]
        found = False
        for item in items:
            if item["uniq_id"] == product["uniq_id"]:
                item["quantity"] += product["quantity"]  # Update quantity
                found = True
                break

        if not found:
            items.append(product)  # Add new product

        total_price = sum(item["quantity"] * item["discounted_price"] for item in items)

        carts_collection.update_one({"_id": cart["_id"]}, {"$set": {"items": items, "total_price": total_price}})
    else:
        new_cart = {
            "user_id": user_id,
            "items": [product],
            "total_price": product["quantity"] * product["discounted_price"]
        }
        carts_collection.insert_one(new_cart)

    updated_cart = carts_collection.find_one({"user_id": user_id})
    return jsonify(serialize_cart(updated_cart))

# Remove item from cart
@cart_blueprint.route('/remove', methods=['POST'])
def remove_from_cart():
    data = request.json
    user_id = data["user_id"]
    product_id = data["uniq_id"]

    cart = carts_collection.find_one({"user_id": user_id})
    if not cart:
        return jsonify({"message": "Cart not found"}), 404

    updated_items = []
    for item in cart["items"]:
        if item["uniq_id"] == product_id:
            if item["quantity"] > 1:
                item["quantity"] -= 1  # Reduce quantity
                updated_items.append(item)
            # If quantity = 1, don't add it to updated_items (removes it)
        else:
            updated_items.append(item)

    total_price = sum(item["quantity"] * item["discounted_price"] for item in updated_items)

    carts_collection.update_one({"_id": cart["_id"]}, {"$set": {"items": updated_items, "total_price": total_price}})

    updated_cart = carts_collection.find_one({"user_id": user_id})
    return jsonify(serialize_cart(updated_cart))
