from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# Email strings are validated without the optional email-validator dependency.
class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Role(str, Enum):
    ADMIN = 'ADMIN'
    MANAGER = 'MANAGER'
    SALES = 'SALES'


class VehicleStatus(str, Enum):
    AVAILABLE = 'AVAILABLE'
    IN_SERVICE = 'IN_SERVICE'
    RESERVED = 'RESERVED'
    SOLD = 'SOLD'


class SaleStatus(str, Enum):
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'


class DriveStatus(str, Enum):
    SCHEDULED = 'SCHEDULED'
    COMPLETED = 'COMPLETED'
    NO_SHOW = 'NO_SHOW'
    CANCELLED = 'CANCELLED'


class PaymentMethod(str, Enum):
    CASH = 'CASH'
    CARD = 'CARD'
    BANK_TRANSFER = 'BANK_TRANSFER'
    FINANCE = 'FINANCE'
    UPI = 'UPI'


def check_email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 254 or '@' not in value or '.' not in value.split('@')[-1] or value.startswith('@'):
        raise ValueError('Enter a valid email address')
    return value


class LoginIn(StrictModel):
    email: str
    password: str
    @field_validator('email')
    @classmethod
    def valid_email(cls, v): return check_email(v)


class BootstrapIn(StrictModel):
    token: str
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=12, max_length=128)
    demo_data: bool = False
    @field_validator('email')
    @classmethod
    def valid_email(cls, v): return check_email(v)


class RegisterIn(StrictModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=12, max_length=128)
    phone: str | None = Field(default=None, max_length=30)
    @field_validator('email')
    @classmethod
    def valid_email(cls, v): return check_email(v)


class PasswordChange(StrictModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)


class UserIn(StrictModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    phone: str | None = Field(default=None, max_length=30)
    role: Role = Role.SALES
    password: str | None = Field(default=None, min_length=12, max_length=128)
    active: bool = True
    @field_validator('email')
    @classmethod
    def valid_email(cls, v): return check_email(v)


class ShowroomIn(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=100)
    address: str = Field(min_length=3, max_length=250)
    phone: str | None = Field(default=None, max_length=30)


class VehicleIn(StrictModel):
    vin: str = Field(min_length=5, max_length=17, pattern=r'^[a-zA-Z0-9-]+$')
    make: str = Field(min_length=1, max_length=60)
    model: str = Field(min_length=1, max_length=60)
    variant: str | None = Field(default=None, max_length=70)
    year: int = Field(ge=1950, le=2100)
    color: str | None = Field(default=None, max_length=40)
    fuel_type: str | None = Field(default=None, max_length=40)
    transmission: str | None = Field(default=None, max_length=40)
    price: Decimal = Field(ge=0, max_digits=13, decimal_places=2)
    mileage: int = Field(default=0, ge=0)
    status: VehicleStatus = VehicleStatus.AVAILABLE
    showroom_id: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=1000)
    @field_validator('vin')
    @classmethod
    def uppercase_vin(cls, v): return v.upper()


class CustomerIn(StrictModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    phone: str = Field(min_length=5, max_length=30)
    city: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=250)
    notes: str | None = Field(default=None, max_length=1000)
    @field_validator('email')
    @classmethod
    def valid_email(cls, v): return check_email(v) if v else None


class SaleIn(StrictModel):
    vehicle_id: int = Field(gt=0)
    customer_id: int = Field(gt=0)
    salesperson_id: int | None = Field(default=None, gt=0)
    sale_price: Decimal = Field(ge=0, max_digits=13, decimal_places=2)
    discount: Decimal = Field(default=Decimal('0'), ge=0, max_digits=13, decimal_places=2)
    payment_method: PaymentMethod
    sale_date: date = Field(default_factory=date.today)
    notes: str | None = Field(default=None, max_length=1000)
    @model_validator(mode='after')
    def valid_discount(self):
        if self.discount > self.sale_price:
            raise ValueError('Discount cannot exceed sale price')
        return self


class TestDriveIn(StrictModel):
    vehicle_id: int = Field(gt=0)
    customer_id: int = Field(gt=0)
    salesperson_id: int | None = Field(default=None, gt=0)
    scheduled_at: datetime
    feedback: str | None = Field(default=None, max_length=1000)


class StatusIn(StrictModel):
    status: str
    feedback: str | None = Field(default=None, max_length=1000)
