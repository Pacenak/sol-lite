"""Remote infrastructure capability layer."""
from .credentials import CredentialReference, CredentialStore, EnvironmentCredentialStore
from .manager import RemoteExecutionRequest, RemoteNodeManager
from .nodes import RemoteNode, RemoteTransport
from .ssh import RemoteCommandResult, SSHTransport

__all__ = [
    "CredentialReference", "CredentialStore", "EnvironmentCredentialStore",
    "RemoteCommandResult", "RemoteExecutionRequest", "RemoteNode", "RemoteNodeManager",
    "RemoteTransport", "SSHTransport",
]
