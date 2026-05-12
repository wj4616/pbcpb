"""
Role — a single role definition in the role system.

Placeholders are defined at design-time.
linked_agent is bound at runtime via config — config edit only, no rebuild required.
null linked_agent is valid (human executes manually). NOT an error.
"""


class Role:
    """
    A single role in the PBCPB role system.

    Attributes:
        placeholder_name: Design-time identifier (e.g., "@architect")
        role_type:        "MULTI_AGENT" | "HUMAN" | "AI_ASSISTED"
        linked_agent:     Runtime agent binding (string or None)
    """

    __slots__ = ("placeholder_name", "role_type", "linked_agent")

    def __init__(self, placeholder_name: str, role_type: str, linked_agent: str = None):
        """
        Args:
            placeholder_name: e.g. "@architect" — defined at design-time
            role_type: exact string from VALID_ROLE_TYPES
            linked_agent: agent name/path for runtime binding; None = human executes
        """
        self.placeholder_name = placeholder_name
        self.role_type = role_type
        self.linked_agent = linked_agent  # None is valid

    def is_human_role(self) -> bool:
        """True if this role is executed by a human."""
        return self.role_type == "HUMAN"

    def is_ai_role(self) -> bool:
        """True if this role is executed by AI (MULTI_AGENT or AI_ASSISTED)."""
        return self.role_type in ("MULTI_AGENT", "AI_ASSISTED")

    def has_agent_binding(self) -> bool:
        """True if a linked_agent is bound. False does NOT indicate an error."""
        return self.linked_agent is not None

    def resolve_executor(self) -> str:
        """
        Return a human-readable description of who executes this role.

        Never raises — null linked_agent produces a clear "manual" description.
        """
        if self.role_type == "HUMAN":
            return f"[human] {self.placeholder_name}"
        elif self.role_type == "MULTI_AGENT":
            agent = self.linked_agent or "(unbound — requires linked_agent in config)"
            return f"[multi-agent] {self.placeholder_name} → {agent}"
        elif self.role_type == "AI_ASSISTED":
            agent = self.linked_agent or "(human-executed, no AI agent bound)"
            return f"[ai-assisted] {self.placeholder_name} → {agent}"
        else:
            return f"[{self.role_type}] {self.placeholder_name}"

    def to_dict(self) -> dict:
        return {
            "placeholder_name": self.placeholder_name,
            "role_type": self.role_type,
            "linked_agent": self.linked_agent,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Role":
        return cls(
            placeholder_name=data["placeholder_name"],
            role_type=data["role_type"],
            linked_agent=data.get("linked_agent"),  # None is valid
        )

    def __repr__(self) -> str:
        return (
            f"Role(placeholder={self.placeholder_name!r}, "
            f"type={self.role_type!r}, "
            f"agent={self.linked_agent!r})"
        )
