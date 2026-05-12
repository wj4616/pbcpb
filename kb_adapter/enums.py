"""
Adapter and role type enumerations for PBCPB.

IMPORTANT: These are the CANONICAL exact-string values.
Any other spelling (RAGMCP, markdown-folder, HUMAN_ONLY, etc.)
raises ConfigError at bind() time — never silent coercion.
"""

# Valid adapter_type strings
VALID_ADAPTER_TYPES = {"RAG_MCP", "MARKDOWN_FOLDER", "JSON_DB", "CUSTOM_API"}

# Valid role_type strings
VALID_ROLE_TYPES = {"MULTI_AGENT", "HUMAN", "AI_ASSISTED"}


class AdapterType:
    """Namespace for adapter_type constant strings."""
    RAG_MCP = "RAG_MCP"
    MARKDOWN_FOLDER = "MARKDOWN_FOLDER"
    JSON_DB = "JSON_DB"
    CUSTOM_API = "CUSTOM_API"


class RoleType:
    """Namespace for role_type constant strings."""
    MULTI_AGENT = "MULTI_AGENT"
    HUMAN = "HUMAN"
    AI_ASSISTED = "AI_ASSISTED"
