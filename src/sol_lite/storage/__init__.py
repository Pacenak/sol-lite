"""Storage authorization and network-location primitives."""
from .authorization import AuthorizedResource, ResourceAuthorizer
from .network import StorageLocation, StorageRegistry

__all__ = ["AuthorizedResource", "ResourceAuthorizer", "StorageLocation", "StorageRegistry"]
