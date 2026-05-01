
def format_restaurant_doc(event_payload: dict) -> dict | None:
    restaurant_id = event_payload.get("restaurant_id")
    if not restaurant_id:
        print("[ELASTICSEARCH RestaurantCreated SYNC]: Missing restaurant_id in event, skipping...")
        return

    addr = event_payload.get("address", {})
    full_address = f"{addr.get('unit', '')} {addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state_code', '')} {addr.get('zip_code', '')}".strip()

    contact = event_payload.get("contact", {})
    contact_details = f"{contact.get("phone", "")} {contact.get("email", "")} {contact.get("website", "")}".strip()
    
    raw_cuisine = event_payload.get("cuisine_type", [])
    categories = raw_cuisine
    if isinstance(categories, str):
        categories = raw_cuisine.strip("{}").split(",")

    document = {
        "restaurant_id" : restaurant_id,
        "restaurant_name" : event_payload.get("restaurant_name"),
        "category": categories,
        "restaurant_address" : full_address,
        "restaurant_contact" : contact_details,
        "owner_id" : event_payload.get("owner_id"),
        "location": {
            "lat": addr.get("geo").get("lat"),
            "lon": addr.get("geo").get("lon")
        }
    }
    return document

def format_menuitem_doc(event_payload: dict) -> dict | None:
    menuitem_id = event_payload.get("menuitem_id")
    if not menuitem_id:
        print("[ELASTICSEARCH MenuItemCreated SYNC]: Missing menuitem_id in event, skipping...")
        return

    document = {
        "menuitem_id" : menuitem_id,
        "restaurant_id" : event_payload["restaurant_id"],  
        "restaurant_name" : event_payload.get("restaurant_name"),  
        "menuitem_name" : event_payload.get("menuitem_name"),
        "menuitem_description" : event_payload.get("menuitem_description"),  
        "menuitem_price" : event_payload.get("menuitem_price")
    }
    return document