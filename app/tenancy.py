"""The tenant context: the only way to say which client a request belongs to.

A TenantContext is built from the authenticated session (the simulated login in the UI, or the
session header in the API). No code path builds one from the user's question text.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.corpus import SHARED_TENANT, tenants

CLIENT_TENANTS: tuple[str, ...] = tuple(tenants())
DISPLAY_NAMES: dict[str, str] = {t.tenant_id: t.display_name for t in tenants().values()}

__all__ = ["CLIENT_TENANTS", "DISPLAY_NAMES", "SHARED_TENANT", "TenantContext"]


class UnknownTenantError(ValueError):
    pass


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str

    def __post_init__(self) -> None:
        if self.tenant_id not in CLIENT_TENANTS:
            raise UnknownTenantError(f"not a client tenant: {self.tenant_id!r}")

    @property
    def visible_tenants(self) -> tuple[str, str]:
        return (self.tenant_id, SHARED_TENANT)
