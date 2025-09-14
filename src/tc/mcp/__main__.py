from mcp.server.fastmcp import FastMCP

from tc.alloy.mcp import register_alloy_list

app = FastMCP(name="thermo-calc")

_ = register_alloy_list(app)


def main():
    """Entry point for the direct execution server."""
    app.run()


if __name__ == "__main__":
    main()
