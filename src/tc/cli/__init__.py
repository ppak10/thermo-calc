from .__main__ import app
from .version import register_version

__all__ = ["app"]

from tc.mcp.cli import app as mcp_app

app.add_typer(mcp_app, name="mcp")

_ = register_version(app)

if __name__ == "__main__":
    app()
