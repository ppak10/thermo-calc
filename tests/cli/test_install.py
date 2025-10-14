import subprocess
from unittest.mock import Mock, patch

import pytest

from tc.cli.install import (
    find_tc_python_whl,
    rename_whl_for_compatibility,
    install_whl,
    install_command,
)


class TestFindTcPythonWhl:
    """Tests for find_tc_python_whl function."""

    def test_finds_whl_file(self, tmp_path):
        """Test that it finds a TC-Python .whl file in a directory."""
        # Create a test .whl file
        whl_file = tmp_path / "TC_Python-2025.2-30-py3-none-any.whl"
        whl_file.touch()

        result = find_tc_python_whl(tmp_path)

        assert result == whl_file

    def test_returns_none_when_no_whl_found(self, tmp_path):
        """Test that it returns None when no .whl file is found."""
        result = find_tc_python_whl(tmp_path)

        assert result is None

    def test_finds_first_whl_when_multiple_exist(self, tmp_path):
        """Test that it returns the first .whl file when multiple exist."""
        whl_file1 = tmp_path / "TC_Python-2025.2-30-py3-none-any.whl"
        whl_file2 = tmp_path / "TC_Python-2024.1-20-py3-none-any.whl"
        whl_file1.touch()
        whl_file2.touch()

        result = find_tc_python_whl(tmp_path)

        assert result in [whl_file1, whl_file2]

    def test_ignores_non_tc_python_whl_files(self, tmp_path):
        """Test that it only matches TC_Python*.whl files."""
        other_whl = tmp_path / "some_other_package-1.0.0-py3-none-any.whl"
        other_whl.touch()

        result = find_tc_python_whl(tmp_path)

        assert result is None


class TestRenameWhlForCompatibility:
    """Tests for rename_whl_for_compatibility function."""

    def test_renames_version_with_hyphen(self, tmp_path):
        """Test that it renames version format from 2-30 to 2.30."""
        original_file = tmp_path / "TC_Python-2025.2-30-py3-none-any.whl"
        original_file.touch()
        expected_file = tmp_path / "TC_Python-2025.2.30-py3-none-any.whl"

        result = rename_whl_for_compatibility(original_file)

        assert result == expected_file
        assert expected_file.exists()
        assert not original_file.exists()

    def test_handles_already_renamed_file(self, tmp_path):
        """Test that it doesn't rename an already compatible file."""
        original_file = tmp_path / "TC_Python-2025.2.30-py3-none-any.whl"
        original_file.touch()

        result = rename_whl_for_compatibility(original_file)

        assert result == original_file
        assert original_file.exists()

    def test_handles_file_without_version_pattern(self, tmp_path):
        """Test that it returns original path if pattern doesn't match."""
        original_file = tmp_path / "TC_Python-unknown-py3-none-any.whl"
        original_file.touch()

        result = rename_whl_for_compatibility(original_file)

        assert result == original_file
        assert original_file.exists()

    # def test_does_not_rename_if_target_exists(self, tmp_path):
    #     """Test that it doesn't rename if target file already exists."""
    #     original_file = tmp_path / "TC_Python-2025.2-30-py3-none-any.whl"
    #     target_file = tmp_path / "TC_Python-2025.2.30-py3-none-any.whl"
    #     original_file.touch()
    #     target_file.touch()
    #
    #     result = rename_whl_for_compatibility(original_file)
    #
    #     # Should return original since target exists
    #     assert result == original_file
    #     assert original_file.exists()
    #     assert target_file.exists()


class TestInstallWhl:
    """Tests for install_whl function."""

    @patch("tc.cli.install.subprocess.run")
    def test_successful_installation(self, mock_run, tmp_path):
        """Test successful installation of .whl file."""
        whl_file = tmp_path / "TC_Python-2025.2.30-py3-none-any.whl"
        whl_file.touch()

        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = install_whl(whl_file)

        assert result is True
        mock_run.assert_called_once_with(
            ["uv", "pip", "install", str(whl_file)],
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("tc.cli.install.subprocess.run")
    def test_installation_failure(self, mock_run, tmp_path):
        """Test handling of installation failure."""
        whl_file = tmp_path / "TC_Python-2025.2.30-py3-none-any.whl"
        whl_file.touch()

        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["uv", "pip", "install"], stderr="Installation failed"
        )

        result = install_whl(whl_file)

        assert result is False

    @patch("tc.cli.install.subprocess.run")
    def test_uv_not_found(self, mock_run, tmp_path):
        """Test handling when uv command is not found."""
        whl_file = tmp_path / "TC_Python-2025.2.30-py3-none-any.whl"
        whl_file.touch()

        mock_run.side_effect = FileNotFoundError()

        result = install_whl(whl_file)

        assert result is False


class TestInstallCommand:
    """Tests for install_command function."""

    @patch("tc.cli.install.install_whl")
    @patch("tc.cli.install.rename_whl_for_compatibility")
    def test_install_with_explicit_whl_path(self, mock_rename, mock_install, tmp_path):
        """Test installation with explicit .whl file path."""
        whl_file = tmp_path / "TC_Python-2025.2-30-py3-none-any.whl"
        whl_file.touch()
        renamed_file = tmp_path / "TC_Python-2025.2.30-py3-none-any.whl"

        mock_rename.return_value = renamed_file
        mock_install.return_value = True

        with pytest.raises(SystemExit) as exc_info:
            install_command(str(whl_file))

        assert exc_info.value.code == 0
        mock_rename.assert_called_once()
        mock_install.assert_called_once_with(renamed_file)

    @patch("tc.cli.install.install_whl")
    @patch("tc.cli.install.rename_whl_for_compatibility")
    @patch("tc.cli.install.find_tc_python_whl")
    def test_install_with_directory_path(
        self, mock_find, mock_rename, mock_install, tmp_path
    ):
        """Test installation with directory path."""
        whl_file = tmp_path / "TC_Python-2025.2-30-py3-none-any.whl"
        whl_file.touch()
        renamed_file = tmp_path / "TC_Python-2025.2.30-py3-none-any.whl"

        mock_find.return_value = whl_file
        mock_rename.return_value = renamed_file
        mock_install.return_value = True

        with pytest.raises(SystemExit) as exc_info:
            install_command(str(tmp_path))

        assert exc_info.value.code == 0
        mock_find.assert_called_once_with(tmp_path)
        mock_rename.assert_called_once()
        mock_install.assert_called_once_with(renamed_file)

    @patch("tc.cli.install.find_tc_python_whl")
    def test_install_with_directory_no_whl_found(self, mock_find, tmp_path):
        """Test installation fails when no .whl file found in directory."""
        mock_find.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            install_command(str(tmp_path))

        assert exc_info.value.code == 1

    def test_install_with_invalid_path(self):
        """Test installation fails with invalid path."""
        with pytest.raises(SystemExit) as exc_info:
            install_command("/nonexistent/path/file.whl")

        assert exc_info.value.code == 1

    @patch("tc.cli.install.install_whl")
    @patch("tc.cli.install.rename_whl_for_compatibility")
    @patch("tc.cli.install.find_tc_python_whl")
    @patch("tc.cli.install.Path.home")
    def test_install_with_default_location(
        self, mock_home, mock_find, mock_rename, mock_install, tmp_path
    ):
        """Test installation with default SDK location."""
        # Setup mock home directory
        mock_home.return_value = tmp_path
        sdk_dir = tmp_path / "Thermo-Calc" / "2025b" / "SDK" / "TC-Python"
        sdk_dir.mkdir(parents=True)

        whl_file = sdk_dir / "TC_Python-2025.2-30-py3-none-any.whl"
        whl_file.touch()
        renamed_file = sdk_dir / "TC_Python-2025.2.30-py3-none-any.whl"

        mock_find.return_value = whl_file
        mock_rename.return_value = renamed_file
        mock_install.return_value = True

        with pytest.raises(SystemExit) as exc_info:
            install_command(None)

        assert exc_info.value.code == 0
        mock_install.assert_called_once_with(renamed_file)

    @patch("tc.cli.install.Path.home")
    def test_install_default_location_not_found(self, mock_home, tmp_path):
        """Test installation fails when default SDK location doesn't exist."""
        mock_home.return_value = tmp_path

        with pytest.raises(SystemExit) as exc_info:
            install_command(None)

        assert exc_info.value.code == 1

    @patch("tc.cli.install.install_whl")
    @patch("tc.cli.install.rename_whl_for_compatibility")
    def test_install_failure_exits_with_error(
        self, mock_rename, mock_install, tmp_path
    ):
        """Test that installation failure causes non-zero exit."""
        whl_file = tmp_path / "TC_Python-2025.2.30-py3-none-any.whl"
        whl_file.touch()

        mock_rename.return_value = whl_file
        mock_install.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            install_command(str(whl_file))

        assert exc_info.value.code == 1
