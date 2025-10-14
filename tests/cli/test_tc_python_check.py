from unittest.mock import patch, MagicMock

import pytest

from tc.cli.tc_python_check import (
    check_tc_python_installed,
    warn_tc_python_not_installed,
)


class TestCheckTcPythonInstalled:
    """Tests for check_tc_python_installed function."""

    @patch("tc.cli.tc_python_check.find_spec")
    def test_returns_true_when_installed(self, mock_find_spec):
        """Test that it returns True when TC-Python is installed."""
        mock_find_spec.return_value = MagicMock()

        result = check_tc_python_installed()

        assert result is True
        mock_find_spec.assert_called_once_with("tc_python")

    @patch("tc.cli.tc_python_check.find_spec")
    def test_returns_false_when_not_installed(self, mock_find_spec):
        """Test that it returns False when TC-Python is not installed."""
        mock_find_spec.return_value = None

        result = check_tc_python_installed()

        assert result is False

    @patch("tc.cli.tc_python_check.find_spec")
    def test_handles_import_error(self, mock_find_spec):
        """Test that it handles ImportError gracefully."""
        mock_find_spec.side_effect = ImportError("Module not found")

        result = check_tc_python_installed()

        assert result is False

    @patch("tc.cli.tc_python_check.find_spec")
    def test_handles_module_not_found_error(self, mock_find_spec):
        """Test that it handles ModuleNotFoundError gracefully."""
        mock_find_spec.side_effect = ModuleNotFoundError("No module named 'tc_python'")

        result = check_tc_python_installed()

        assert result is False

    @patch("tc.cli.tc_python_check.find_spec")
    def test_handles_value_error(self, mock_find_spec):
        """Test that it handles ValueError gracefully."""
        mock_find_spec.side_effect = ValueError("Invalid module name")

        result = check_tc_python_installed()

        assert result is False


class TestWarnTcPythonNotInstalled:
    """Tests for warn_tc_python_not_installed function."""

    @patch("tc.cli.tc_python_check.check_tc_python_installed")
    @patch("tc.cli.tc_python_check.console")
    def test_displays_warning_when_not_installed(self, mock_console, mock_check):
        """Test that it displays a warning when TC-Python is not installed."""
        mock_check.return_value = False

        warn_tc_python_not_installed()

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "Warning" in call_args
        assert "TC-Python is not installed" in call_args
        assert "tcalc install" in call_args

    @patch("tc.cli.tc_python_check.check_tc_python_installed")
    @patch("tc.cli.tc_python_check.console")
    def test_no_warning_when_installed(self, mock_console, mock_check):
        """Test that no warning is displayed when TC-Python is installed."""
        mock_check.return_value = True

        warn_tc_python_not_installed()

        mock_console.print.assert_not_called()
