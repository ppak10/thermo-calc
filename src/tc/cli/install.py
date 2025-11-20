import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()


def get_default_sdk_path() -> Path:
    """Get the default TC-Python SDK path based on the operating system."""
    system = platform.system()

    if system == "Darwin":  # macOS
        return Path("/Users/Shared/Thermo-Calc/2025b/SDK/TC-Python")
    else:  # Linux/Ubuntu and others
        return Path.home() / "Thermo-Calc" / "2025b" / "SDK" / "TC-Python"


def get_tc_home_path(sdk_path: Path) -> Path:
    """Get the TC_HOME path from the SDK path (grandparent of TC-Python)."""
    # SDK path is .../2025b/SDK/TC-Python, TC_HOME is .../2025b
    return sdk_path.parent.parent


def get_shell_profile() -> Optional[Path]:
    """Get the appropriate shell profile file for the current user."""
    home = Path.home()
    shell = Path(
        subprocess.run(
            ["echo", "$SHELL"], shell=True, capture_output=True, text=True
        ).stdout.strip()
        or "/bin/zsh"
    )

    # Check common shell profiles
    if "zsh" in str(shell):
        return home / ".zshrc"
    elif "bash" in str(shell):
        # macOS uses .bash_profile, Linux uses .bashrc
        if platform.system() == "Darwin":
            return home / ".bash_profile"
        return home / ".bashrc"
    return None


def set_tc_home_env(tc_home_path: Path) -> bool:
    """Set TC25B_HOME environment variable in the user's shell profile."""
    profile_path = get_shell_profile()

    if not profile_path:
        console.print(
            "[yellow]![/yellow] Could not determine shell profile. "
            f"Please manually add: export TC25B_HOME={tc_home_path}"
        )
        return False

    env_line = f'export TC25B_HOME="{tc_home_path}"'

    # Check if already set
    if profile_path.exists():
        content = profile_path.read_text()
        if "TC25B_HOME" in content:
            console.print(
                f"[yellow]![/yellow] TC25B_HOME already set in {profile_path}"
            )
            return True

    # Append to profile
    try:
        with open(profile_path, "a") as f:
            f.write(f"\n# Thermo-Calc environment variable\n{env_line}\n")
        console.print(f"[green]✓[/green] Added TC25B_HOME to {profile_path}")
        console.print(
            f"[blue]Note:[/blue] Run 'source {profile_path}' or restart your terminal to apply"
        )
        return True
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to update {profile_path}: {e}")
        return False


def find_tc_python_whl(sdk_path: Path) -> Optional[Path]:
    """Find TC-Python .whl file in the given directory."""
    whl_files = list(sdk_path.glob("TC_Python*.whl"))
    if not whl_files:
        return None
    return whl_files[0]


def rename_whl_for_compatibility(whl_path: Path) -> Path:
    """Rename .whl file to replace version format 2-30 with 2.30."""
    # Pattern to match version like 2025.2-30
    pattern = r"(TC_Python-\d+\.\d+)-(\d+)"
    match = re.search(pattern, whl_path.name)

    if not match:
        # If no match, return original path
        return whl_path

    # Replace hyphen with dot in version number
    new_name = re.sub(pattern, r"\1.\2", whl_path.name)
    new_path = whl_path.parent / new_name

    # Rename the file
    if whl_path != new_path and not new_path.exists():
        shutil.move(str(whl_path), str(new_path))
        console.print(f"[green]✓[/green] Renamed: {whl_path.name} → {new_name}")

    return new_path


def install_whl(whl_path: Path) -> bool:
    """Install .whl file using uv pip install."""
    try:
        console.print(f"[blue]Installing[/blue] {whl_path.name}...")
        result = subprocess.run(
            ["uv", "pip", "install", str(whl_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        console.print(f"[green]✓[/green] Successfully installed {whl_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗[/red] Installation failed: {e.stderr}", style="red")
        return False
    except FileNotFoundError:
        console.print(
            "[red]✗[/red] uv command not found. Please install uv first.", style="red"
        )
        return False


def install_command(
    path: Optional[str] = typer.Argument(
        None,
        help="Path to TC-Python .whl file or SDK directory. If not provided, searches default location.",
    )
):
    """
    Install TC-Python from .whl file.

    Automatically finds and renames TC-Python .whl files to be compatible with uv,
    then installs them.
    """
    sdk_path = None

    if path:
        # User provided explicit path
        provided_path = Path(path).expanduser().resolve()

        if provided_path.is_file() and provided_path.suffix == ".whl":
            # Direct .whl file provided
            whl_path = rename_whl_for_compatibility(provided_path)
            success = install_whl(whl_path)
            if success:
                # Try to determine TC_HOME from .whl path
                sdk_path = provided_path.parent
                tc_home = get_tc_home_path(sdk_path)
                if tc_home.exists():
                    set_tc_home_env(tc_home)
            sys.exit(0 if success else 1)
        elif provided_path.is_dir():
            # Directory provided, search for .whl
            sdk_path = provided_path
            whl_path = find_tc_python_whl(provided_path)
            if not whl_path:
                console.print(
                    f"[red]✗[/red] No TC-Python .whl file found in {provided_path}",
                    style="red",
                )
                sys.exit(1)
        else:
            console.print(f"[red]✗[/red] Invalid path: {path}", style="red")
            sys.exit(1)
    else:
        # Search default location based on OS
        sdk_path = get_default_sdk_path()

        if not sdk_path.exists():
            console.print(
                f"[red]✗[/red] Default SDK path not found: {sdk_path}\n"
                f"Please provide the path explicitly: [cyan]tcalc install <path>[/cyan]",
                style="red",
            )
            sys.exit(1)

        whl_path = find_tc_python_whl(sdk_path)
        if not whl_path:
            console.print(
                f"[red]✗[/red] No TC-Python .whl file found in {sdk_path}",
                style="red",
            )
            sys.exit(1)

    # Rename and install
    whl_path = rename_whl_for_compatibility(whl_path)
    success = install_whl(whl_path)

    # Set TC25B_HOME environment variable
    if success and sdk_path:
        tc_home = get_tc_home_path(sdk_path)
        if tc_home.exists():
            set_tc_home_env(tc_home)

    sys.exit(0 if success else 1)


def register_install(app: typer.Typer):
    """Register the install command with the main app."""
    app.command(name="install", help="Install TC-Python from .whl file")(
        install_command
    )
