# Device schemas
from typing import List
from enum import Enum
import keyword
from pydantic import BaseModel, EmailStr
class DeviceType(Enum):
    MASTER = 'MASTER'
    SLAVE = 'SLAVE'
    GUEST = 'GUEST'
class DataType(Enum):
    STRING = 'string'
    FLOAT = 'float'
    INTEGER = 'integer'
    BOOLEAN = 'boolean'
    DATETIME = 'datetime'
    JSON = 'json'
class PinType(Enum):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
class DeviceRegister(BaseModel):
    device_name: str
    device_type: DeviceType  # 'master' or 'slave'
    # mac_address: Optional[str] = None
    # device_config: Optional[dict] = {}
class DeviceUpdateRequest(BaseModel):
    device_token: str
    device_name: str
    device_type: DeviceType
    is_active : bool
class PinConfig(BaseModel):
    # device_token: str
    virtual_pin : int
    pin_label : str
    pin_type: PinType
    data_type: DataType
    ai_keywords : str
# class DeviceConfigResponse(BaseModel):
#     device_token: str
#     virtual_pin : int
#     pin_label : str
#     pin_type: PinType
#     data_type: DataType
#     ai_keywords : str
class DeviceConfigRequest(BaseModel):
    device_token: str
    pins: List[PinConfig]
class DeviceResponse(BaseModel):
    id: str
    device_name: str
    device_type: DeviceType
    device_token: str
    is_online: bool
    last_seen: str
    created_at: str

class SensorData(BaseModel):
    device_token: str
    virtual_pin : int
    value: str

# class CommandData(BaseModel):
#     action: str
#     device_name: str
#     value: Optional[float] = None
