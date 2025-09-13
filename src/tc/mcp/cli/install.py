import shutil
import subprocess
import typer

from importlib.resources import files
from typing_extensions import Annotated
from pathlib import Path
from rich import print as rprint


def register_mcp_install(app: typer.Typer):
    @app.command(name="install")
    def mcp_development(
        client: Annotated[
            str,
            typer.Option("--client", help="Target client to install for."),
        ] = "claude-code",
        include_agent: Annotated[bool, typer.Option("--include-agent")] = True,
        project_path: Annotated[str | None, typer.Option("--project-path")] = None,
    ) -> None:
        import tc

        from tc import data

        # Determine project root path
        if project_path:
            tc_path = Path(project_path)
        else:
            # Path(tc.__file__) extcple:
            # /mnt/tc/GitHub/thermo-calc-agent/.venv/lib/python3.13/site-packages/tc
            # Going up 5 levels to get to the project root
            tc_path = Path(tc.__file__).parents[5]

        rprint(
            f"[bold green]Using `thermo-calc` packaged under project path:[/bold green] {tc_path}"
        )

        match client:
            case "claude-code":
                # TODO: Handle case if agent already exists
                # (i.e. auto remove existing agent if updating.)
                try:
                    claude_cmd = [
                        "claude",
                        "mcp",
                        "add-json",
                        "tc",
                        f'{{"command": "uv", "args": ["--directory", "{tc_path}", "run", "-m", "tc.mcp"]}}',
                    ]

                    rprint(f"[blue]Running command:[/blue] {' '.join(claude_cmd)}")
                    subprocess.run(claude_cmd, check=True)

                    if include_agent:
                        # Copies premade agent configuration to `.claude/agents`
                        agent_file = files(data) / "mcp" / "agent.md"
                        claude_agents_path = tc_path / ".claude" / "agents"
                        claude_agents_path.mkdir(parents=True, exist_ok=True)
                        claude_agent_config_path = claude_agents_path / "tc.md"
                        with (
                            agent_file.open("rb") as src,
                            open(claude_agent_config_path, "wb") as dst,
                        ):
                            shutil.copyfileobj(src, dst)
                        rprint(
                            f"[bold green]Installed agent under path:[/bold green] {claude_agent_config_path}"
                        )

                except subprocess.CalledProcessError as e:
                    rprint(f"[red]Command failed with return code {e.returncode}[/red]")
                    rprint(f"[red]Error output: {e.stderr}[/red]" if e.stderr else "")
                except Exception as e:
                    rprint(f"[red]Unexpected error running command:[/red] {e}")

            case _:
                rprint(
                    "[yellow]No client provided.[/yellow]\n"
                    "[bold]Please specify where to install with one of the following:[/bold]\n"
                    "  • [green]--client claude-code[/green] to install for Claude Code\n"
                    "  • Other options coming soon..."
                )

    _ = app.command(name="install")(mcp_development)
    return mcp_development
