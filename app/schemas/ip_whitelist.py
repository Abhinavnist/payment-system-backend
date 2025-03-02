from typing import Optional, List, Literal
from pydantic import BaseModel, IPvAnyAddress, Field


class IPWhitelistBase(BaseModel):
    ip_addresses: List[str]
    operation: Literal["add", "remove", "replace"] = Field(
        description="Operation to perform: 'add' to append IPs, 'remove' to delete IPs, 'replace' to set new list"
    )


class IPWhitelistCreate(IPWhitelistBase):
    pass


class IPWhitelistUpdate(IPWhitelistBase):
    pass


class IPWhitelist(BaseModel):
    ip_addresses: List[str]

    class Config:
        from_attributes = True 