class SOLLiteError(Exception): pass
class ConfigurationError(SOLLiteError): pass
class PermissionDenied(SOLLiteError): pass
class ApprovalRequired(SOLLiteError):
    def __init__(self,message,request=None): super().__init__(message); self.request=request
class ToolExecutionError(SOLLiteError): pass
class AgentError(SOLLiteError): pass
class ModelError(SOLLiteError): pass
class TaskError(SOLLiteError): pass
class SecurityError(SOLLiteError): pass
