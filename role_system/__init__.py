"""
Role System Abstraction — PBCPB Unified

Provides RoleSystem.from_config(config) as the entry point.

Supported role_type values (exact strings only):
    MULTI_AGENT  — role executed by a multi-agent swarm
    HUMAN        — role executed manually by a human
    AI_ASSISTED  — role executed by human+AI collaboration

Mixed configurations (MULTI_AGENT + HUMAN + AI_ASSISTED) coexist without conflict.
null linked_agent is valid — human executes manually. NOT an error.
"""

from .system import RoleSystem
from .role import Role

__all__ = ["RoleSystem", "Role"]
