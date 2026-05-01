from pydantic import BaseModel, ConfigDict

class DriverProfileCreate(BaseModel):
    license_number: str
    is_active: bool = True
    vehicle_details: str

class DriverProfileResponse(BaseModel):
    id: int
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)