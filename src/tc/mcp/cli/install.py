import typer

from typing_extensions import Annotated
from pathlib import Path
from rich import print as rprint

from tc.mcp.install import install


def register_mcp_install(app: typer.Typer):
    @app.command(name="install")
    def mcp_install(
        client: Annotated[
            str, typer.Argument(help="Target client to install for.")
        ] = "claude-code",
        include_agent: Annotated[bool, typer.Option("--include-agent")] = False,
        project_path: Annotated[str | None, typer.Option("--project-path")] = None,
        dev: Annotated[bool, typer.Option("--dev")] = False,
    ) -> None:
        import tc

        # Determine project root path
        if dev:
            # /Users/ppak/GitHub/thermo-calc on mac mini
            tc_path = Path(tc.__file__).parents[2]
        elif project_path:
            tc_path = Path(project_path)
        else:
            # Path(tc.__file__) example:
            # /GitHub/thermo-calc/.venv/lib/python3.13/site-packages/tc
            # Going up 5 levels to get to the project root
            tc_path = Path(tc.__file__).parents[5]

        rprint(
            f"[bold green]Using `thermo-calc` packaged under project path:[/bold green] {tc_path}"
        )

        install(tc_path, client=client, include_agent=include_agent)

    _ = app.command(name="install")(mcp_install)
    return mcp_install
