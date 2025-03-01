from typing import Optional, List
from pydantic import BaseModel, IPvAnyAddress


class IPWhitelistBase(BaseModel):
    ip_address: IPvAnyAddress
    description: Optional[str] = None
    is_active: bool = True


class IPWhitelistCreate(IPWhitelistBase):
    pass


class IPWhitelistUpdate(IPWhitelistBase):
    ip_address: Optional[IPvAnyAddress] = None
    is_active: Optional[bool] = None


class IPWhitelist(IPWhitelistBase):
    id: int

    class Config:
        from_attributes = True 