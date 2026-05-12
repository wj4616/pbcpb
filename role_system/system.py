"""
RoleSystem — loaded role system abstraction.

Loaded via RoleSystem.from_config(config_dict) at AdapterSession.bind() time.
Provides role lookup, placeholder resolution, and executor description.

Rules:
    - Mixed role types (MULTI_AGENT + HUMAN + AI_ASSISTED) coexist without conflict
    - null linked_agent is valid — NEVER an error
    - Updating linked_agent requires only config edit, no rebuild
    - Exact-string enum validation: pseudo-values raise ConfigError at bind() time
"""

from .role import Role
from kb_adapter.errors import ConfigError
from kb_adapter.enums import VALID_ROLE_TYPES


class RoleSystem:
    """
    Loaded role system. Holds all role definitions for a PBCPB config.

    Construction: RoleSystem.from_config(config_dict) → RoleSystem

    Supports mixed configurations — all role_type values coexist without conflict.
    """

    def __init__(self, syntax_mode: str, syntax_pattern: str, roles: list):
        """
        Args:
            syntax_mode: "@name" or "custom"
            syntax_pattern: user-defined pattern if syntax_mode == "custom"
            roles: list of Role objects
        """
        self._syntax_mode = syntax_mode
        self._syntax_pattern = syntax_pattern
        self._roles = {r.placeholder_name: r for r in roles}

    @classmethod
    def from_config(cls, config: dict) -> "RoleSystem":
        """
        Build RoleSystem from a role_system config block.

        Validates role_type exact strings. Raises ConfigError on invalid values.

        Args:
            config: The role_system config dict

        Returns:
            RoleSystem instance

        Raises:
            ConfigError: invalid role_type or missing placeholder_name
        """
        syntax_mode = config.get("syntax_mode", "@name")
        syntax_pattern = config.get("syntax_pattern", "@{name}")

        roles_raw = config.get("roles", [])
        roles = []

        for i, role_data in enumerate(roles_raw):
            placeholder_name = role_data.get("placeholder_name")
            if not placeholder_name:
                raise ConfigError(
                    f"role_system.roles[{i}] missing required 'placeholder_name'",
                    offending_field=f"role_system.roles[{i}].placeholder_name",
                    adapter_type=None,
                )

            role_type = role_data.get("role_type")
            if role_type not in VALID_ROLE_TYPES:
                raise ConfigError(
                    f"role_system.roles[{i}].role_type '{role_type}' is not valid. "
                    f"Must be one of: {sorted(VALID_ROLE_TYPES)} (exact strings, case-sensitive). "
                    f"Common mistakes: HUMAN_ONLY, MULTIAGENT, ai-assisted.",
                    offending_field=f"role_system.roles[{i}].role_type",
                    adapter_type=None,
                )

            # linked_agent=None is valid — not an error
            linked_agent = role_data.get("linked_agent")  # May be None

            roles.append(Role(
                placeholder_name=placeholder_name,
                role_type=role_type,
                linked_agent=linked_agent,
            ))

        return cls(syntax_mode=syntax_mode, syntax_pattern=syntax_pattern, roles=roles)

    @property
    def syntax_mode(self) -> str:
        return self._syntax_mode

    @property
    def syntax_pattern(self) -> str:
        return self._syntax_pattern

    def get_role(self, placeholder_name: str) -> Role | None:
        """
        Look up a role by placeholder name.

        Args:
            placeholder_name: e.g. "@architect"

        Returns:
            Role or None if not found
        """
        return self._roles.get(placeholder_name)

    def all_roles(self) -> list:
        """Return all roles as a list."""
        return list(self._roles.values())

    def roles_by_type(self, role_type: str) -> list:
        """
        Return all roles of a given type.

        Args:
            role_type: "MULTI_AGENT" | "HUMAN" | "AI_ASSISTED"

        Returns:
            list of Role objects
        """
        return [r for r in self._roles.values() if r.role_type == role_type]

    def resolve_placeholder(self, text: str) -> str:
        """
        Replace placeholder names in text with executor descriptions.

        e.g. "@architect does X" → "[multi-agent] @architect → planner-agent does X"

        Args:
            text: Text containing placeholder names

        Returns:
            Text with placeholders resolved to executor descriptions
        """
        result = text
        for placeholder, role in self._roles.items():
            result = result.replace(placeholder, role.resolve_executor())
        return result

    def bind_agent(self, placeholder_name: str, agent_name: str):
        """
        Bind a linked_agent to a role at runtime (config-edit equivalent).

        This method simulates what a config edit achieves — no rebuild required.
        In production, users edit pbcpb.config.json and re-call bind().

        Args:
            placeholder_name: Role to update
            agent_name: New linked_agent value (or None to unbind)

        Raises:
            ConfigError: if placeholder_name not found
        """
        role = self._roles.get(placeholder_name)
        if role is None:
            raise ConfigError(
                f"Cannot bind agent to unknown placeholder '{placeholder_name}'. "
                f"Known placeholders: {sorted(self._roles.keys())}",
                offending_field="role_system.roles[*].placeholder_name",
                adapter_type=None,
            )
        role.linked_agent = agent_name

    def summary(self) -> dict:
        """Return a summary dict of the role system state."""
        return {
            "syntax_mode": self._syntax_mode,
            "syntax_pattern": self._syntax_pattern,
            "role_count": len(self._roles),
            "roles": [r.to_dict() for r in self._roles.values()],
            "by_type": {
                rt: [r.placeholder_name for r in self.roles_by_type(rt)]
                for rt in ("MULTI_AGENT", "HUMAN", "AI_ASSISTED")
            },
        }
