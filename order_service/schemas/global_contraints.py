from decimal import Decimal
from typing import Annotated
from pydantic import Field, StringConstraints

MobileNumberStr = Annotated[
    str,
    StringConstraints(
        pattern=r'^\+?[1-9]\d{1,14}$',
        min_length=10,
        max_length=15,
        strip_whitespace=True,
    )
]

PasswordStr = Annotated[
    str,
    StringConstraints(
        min_length=8,
        max_length=128,
    )
]

EmailStr = Annotated[
    str,
    StringConstraints(
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        max_length=254,
        strip_whitespace=True,
    )
]

PriceDecimal = Annotated[
    Decimal,
    Field(
        gt=0, 
        max_digits=10, 
        decimal_places=2
    )
]

QuantityInt = Annotated[
    int,
    Field(
        gt=0,
        le=1000
    )
]

