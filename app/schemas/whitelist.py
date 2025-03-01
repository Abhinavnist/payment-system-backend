from typing import List, Literal
from pydantic import BaseModel, IPvAnyAddress, validator


class IPWhitelistUpdate(BaseModel):
    """Schema for updating IP whitelist"""
    operation: Literal["add", "remove", "replace"]
    ip_addresses: List[str]
    
    @validator('ip_addresses', each_item=True)
    def validate_ip(cls, v):
        """Validate each IP address"""
        try:
            IPvAnyAddress(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address: {v}")