from .__main__ import app
from .install import register_mcp_install
from .uninstall import register_mcp_uninstall

_ = register_mcp_install(app)
_ = register_mcp_uninstall(app)

__all__ = ["app"]
