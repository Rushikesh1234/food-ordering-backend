from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User

from app.schemas.order import OrderCreate, OrderResponse

from app.services.validate_service import validate_restaurant, validate_menu_items

def create_order(db: Session, user: User, order_data: OrderCreate) -> OrderResponse:

    try:
        validate_restaurant(db, order_data.restaurant_id)
        total_amount, validated_items = validate_menu_items(
            db, order_data.restaurant_id, order_data.order_items
        )

        new_order = Order(
            user_id=user.id,
            restaurant_id=order_data.restaurant_id,
            total_amount=total_amount,
            status='CREATED'
        )

        db.add(new_order)
        db.flush()

        for item in validated_items:
            order_item = OrderItem(
                order_id=new_order.id,
                menu_item_id=item["menu_item"].id,
                quantity=item["quantity"],
                price=item["price"]
            )
            db.add(order_item)
        
        db.commit()
        db.refresh(new_order)
        return OrderResponse.model_validate(new_order)
    
    except HTTPException as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Order creation failed") from e