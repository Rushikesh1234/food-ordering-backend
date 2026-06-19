import json
import uuid
from typing import cast
from confluent_kafka import Consumer
from sqlalchemy.orm import Session

from order_service.config.redis_config import redis_client, IDEMPOTENCY_TTL

from order_service.db.session import SessionLocal

from order_service.models.order import Order, OrderStatus
from order_service.models.order_item import OrderItem
from order_service.models.outbox import Outbox
from order_service.models.local_sync import LocalRestaurant, LocalMenuItem, LocalDriver

from order_service.schemas.order_events import OrderPaidEvent, OrderItemPayload

from order_service.logic.update_order_status_service import validate_transitions

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPICS = ["events.Restaurant", "events.MenuItem", "events.User", "events.DriverAssignment", "events.Payment", "events.KitchenOrder"]
GROUP_ID = "order-service-sync-group"

def creat_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True
    })

def is_duplicate_event(event_id: int) -> bool:
    key = f"order_service:proc:{event_id}"
    is_new = redis_client.set(key, "true", nx=True, ex=IDEMPOTENCY_TTL)
    return is_new is None

def process_event(db:Session, event_payload: dict):

    event_type = event_payload.get("event_type")

    if event_type == "RestaurantCreated" or event_type == "RestaurantUpdated":
        restaurant_id = event_payload["restaurant_id"]
        restaurant = db.query(LocalRestaurant).filter(LocalRestaurant.id == restaurant_id).first()

        if not restaurant:
            restaurant = LocalRestaurant(
                id=restaurant_id
            )
            db.add(restaurant)
        
        restaurant.name = event_payload["restaurant_name"]
        restaurant.owner_id = event_payload["owner_id"]
        restaurant.is_active = event_payload["is_active"]

        print(f"[Order SYNC] Synced Restaurant - ID: {restaurant_id}, Name: {restaurant.name}, Owner_ID: {restaurant.owner_id}, Is_Active: {restaurant.is_active}")

    elif event_type == "MenuItemCreated" or event_type == "MenuItemUpdated":
        menu_item_id = event_payload["menuitem_id"]
        menu_item = db.query(LocalMenuItem).filter(LocalMenuItem.id == menu_item_id).first()

        if not menu_item:
            menu_item = LocalMenuItem(
                id = menu_item_id
            )
            db.add(menu_item)
        
        menu_item.name = event_payload["menuitem_name"]
        menu_item.restaurant_id = event_payload["restaurant_id"]
        menu_item.price = event_payload["menuitem_price"]
        menu_item.is_available = event_payload.get("is_available", True)

        print(f"[Order SYNC] Synced MenuItem - ID: {menu_item.id}, Name: {menu_item.name}, Restaurant_id: {menu_item.restaurant_id}, Price: {menu_item.price}, Is_Available: {menu_item.is_available}")
    
    elif (event_type == "UserCreated" or event_type == "UserUpdated") and event_payload.get("role") == "driver" :
        driver_id = event_payload["user_id"]
        driver = db.query(LocalDriver).filter(LocalDriver.id == driver_id).first()

        if not driver:
            driver = LocalDriver(
                id = driver_id
            )
            db.add(driver)

        driver.is_active = event_payload["is_active"]
        driver.name = event_payload["name"]

        print(f"[Order SYNC] Synced Driver Detail - ID: {driver.id}, Is_Active: {driver.is_active}, Name: {driver.name}")
    
    elif event_type == "DriverAssigned":
        order_id = event_payload.get("order_id")
        driver_id = event_payload.get("driver_id")

        print(f"[ORDER SYNC] Processing Assignment: Order {order_id} -> Driver {driver_id}")

        order = db.query(Order).filter(
            Order.id == order_id,
            Order.status == OrderStatus.READY
        ).first()
        
        if not order:
            print(f"[ORDER SYNC] WARNING: Order {order_id} not found or not in READY status. Skipping.")
            return
        
        driver = db.query(LocalDriver).filter(LocalDriver.id == driver_id).first()
        if not driver:
            print(f"[ORDER SYNC] ERROR: Driver {driver_id} not found in local_drivers sync table.")
            return       
        
        try:
            order.driver_id = driver.id
            order.status = cast(OrderStatus, OrderStatus.ASSIGNED)
            print(f"[ORDER SYNC] SUCCESS: Order {order_id} status updated to ASSIGNED with Driver {driver_id}")
        except Exception as e:
            print(f"[ORDER SYNC] CRITICAL ERROR: Could not update order {order_id}: {e}")
    
    elif event_type == "PaymentSucceeded":
        stripe_payment_intent_id = event_payload.get("stripe_payment_intent_id")
        order_id = event_payload.get("order_id")
        order_amount_paid = event_payload.get("amount_paid")

        order = db.query(Order).filter(
            Order.id == order_id,
            Order.stripe_payment_intent_id == stripe_payment_intent_id
        ).first()

        if not order:
            print(f"[ORDER SYNC] ERROR: Received payment for unknown intent {stripe_payment_intent_id}")
            return

        if order_amount_paid is None or order_amount_paid != order.total_amount:
            print(f"[ORDER SYNC] ERROR: Payment amount {order_amount_paid} does not match order total {order.total_amount} for Order {order_id}")
            return

        if order.status == OrderStatus.CREATED:
            order.status = cast(OrderStatus, OrderStatus.PAID)

            order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

            if not order_items:
                print(f"[ORDER SYNC] WARNING: No order items found for Order {order.id} during payment sync.")
            else:
                event_items_payload = []
                for item in order_items:   
                    event_items_payload.append(
                        OrderItemPayload(
                            item_id=cast(int, item.menu_item_id),
                            quantity=cast(int, item.quantity),
                            price_per_unit=cast(int, item.price)
                        )
                    )
                
                event_data = OrderPaidEvent(
                    order_id = cast(int, order.id),
                    user_id = cast(int, order.user_id),
                    restaurant_id = cast(int, order.restaurant_id),
                    items = event_items_payload,
                    total_amount = cast(int, order.total_amount)
                )

                event_entry = Outbox(
                    id = uuid.uuid4(),
                    aggregatetype = "Order",
                    aggregateid = str(order.id),
                    type = event_data.event_type,
                    payload = event_data.model_dump(mode='json')
                )
                
                db.add(event_entry)

                print(f"[ORDER SYNC] SUCCESS: Order {order.id} status updated to PAID after payment success and update in outbox for restaurant service.")       
        else:
            print(f"[ORDER SYNC] WARNING: Order {order.id} already in state {order.status}. Ignoring.")

    elif event_type == "OrderAcceptedByRestaurant":
        order_id = event_payload.get("order_id")
        restaurant_id = event_payload.get("restaurant_id")

        order = db.query(Order).filter(
            Order.id == order_id,
            Order.restaurant_id == restaurant_id
        ).first()

        if not order:
            print(f"[ORDER SYNC] ERROR: Received OrderAcceptedByRestaurant for unknown order {order_id} and restaurant {restaurant_id}")
            return
        
        if order.status != OrderStatus.PAID:
            print(f"[ORDER SYNC] WARNING: Received OrderAcceptedByRestaurant for Order {order_id} in status {order.status}. Expected PAID. Ignoring.")
            return

        try:
            old_status = str(order.status.value)
            validate_transitions(old_status, OrderStatus.ACCEPTED.value)
            order.status = cast(OrderStatus, OrderStatus.ACCEPTED)
            print(f"[ORDER SYNC] SUCCESS: Order {order_id} status updated to ACCEPTED based on Restaurant acceptance.")

            validate_transitions(str(order.status.value), OrderStatus.PREPARING.value)
            order.status = cast(OrderStatus, OrderStatus.PREPARING)
            print(f"[ORDER SYNC] SUCCESS: Order {order_id} status moved to PREPARING state")

        except Exception as e:
            print(f"[ORDER SYNC] CRITICAL ERROR: Could not update order {order_id} to ACCEPTED: {e}")

    elif event_type == "OrderReadyByRestaurant":
        order_id = event_payload.get("order_id")
        restaurant_id = event_payload.get("restaurant_id")

        order = db.query(Order).filter(
            Order.id == order_id,
            Order.restaurant_id == restaurant_id
        ).first()

        if not order:
            print(f"[ORDER SYNC] ERROR: Received OrderReadyByRestaurant for unknown order {order_id} and restaurant {restaurant_id}")
            return
        
        if order.status != OrderStatus.PREPARING:
            print(f"[ORDER SYNC] WARNING: Received OrderReadyByRestaurant for Order {order_id} in status {order.status}. Expected PREPARING. Ignoring.")
            return
        
        old_status = str(order.status.value)
        validate_transitions(old_status, OrderStatus.READY.value)

        try:
            order.status = cast(OrderStatus, OrderStatus.READY)
            print(f"[ORDER SYNC] SUCCESS: Order {order_id} status updated to ACCEPTED based on Restaurant acceptance.")
        except Exception as e:
            print(f"[ORDER SYNC] CRITICAL ERROR: Could not update order {order_id} to ACCEPTED: {e}")



    db.commit()
    print(f"[ORDER SYNC] Synced {event_type} to Order Service")

def start_consumer():

    consumer = creat_consumer()
    consumer.subscribe(TOPICS)
    print("[Order SYNC] Kafka Sync Service started...")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print(f"[ORDER SYNC] Consumer error: {msg.error()}")
                continue

            message = msg.value()

            if message is not None:
                try:
                    event = json.loads(message.decode("utf-8"))
                    event_payload = event.get("payload", {})

                    event_id = event_payload.get("event_id")
                    
                    if not event_id:
                        print("[ORDER SYNC] Received evetn without event_id, skipping...")
                        continue
                    
                    if is_duplicate_event(event_id):
                        print(f"[ORDER SYNC] Duplicate event {event_id} detected, skipping...")
                        continue   

                    with SessionLocal() as db:
                        try:
                            process_event(
                                db=db,
                                event_payload=event_payload
                            )
                        except Exception as e:
                            db.rollback()
                            print(f"[ORDER SYNC] Error processing event: {e}")

                except json.JSONDecodeError as e:
                    print(f"[ORDER SYNC] Failed to parse JSON: {e}")
            else:    
                print("[ORDER SYNC] Received a tombstone or enpty message.")
    
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()


