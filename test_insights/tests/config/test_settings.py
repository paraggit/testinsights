"""Test configuration and settings."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from test_insights.config.settings import Settings


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        with patch.dict(
            os.environ,
            {"REPORTPORTAL_URL": "https://test.com", "REPORTPORTAL_API_TOKEN": "test_token"},
        ):
            settings = Settings()

            assert settings.api_host == "0.0.0.0"
            assert settings.api_port == 8000
            assert settings.llm_provider == "ollama"
            assert settings.custom_api_title == "TestInsight API"
            assert settings.enable_docs is True

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        test_env = {
            "REPORTPORTAL_URL": "https://custom.reportportal.com",
            "REPORTPORTAL_API_TOKEN": "custom_token_123",
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "LLM_PROVIDER": "openai",
            "CUSTOM_API_TITLE": "Custom API",
            "DEV_MODE": "true",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()

            assert settings.reportportal_url == "https://custom.reportportal.com"
            assert settings.reportportal_api_token == "custom_token_123"
            assert settings.api_host == "127.0.0.1"
            assert settings.api_port == 9000
            assert settings.llm_provider == "openai"
            assert settings.custom_api_title == "Custom API"
            assert settings.dev_mode is True

    def test_case_insensitive_env_vars(self):
        """Test that environment variables are case insensitive."""
        test_env = {
            "reportportal_url": "https://test.com",
            "reportportal_api_token": "test_token",
            "api_host": "localhost",
            "llm_provider": "anthropic",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()

            assert settings.reportportal_url == "https://test.com"
            assert settings.api_host == "localhost"
            assert settings.llm_provider == "anthropic"

    def test_path_settings(self):
        """Test Path-type settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_env = {
                "REPORTPORTAL_URL": "https://test.com",
                "REPORTPORTAL_API_TOKEN": "test_token",
                "CHROMA_PERSIST_DIRECTORY": temp_dir,
                "BACKUP_DIRECTORY": f"{temp_dir}/backups",
            }

            with patch.dict(os.environ, test_env):
                settings = Settings()

                assert isinstance(settings.chroma_persist_directory, Path)
                assert str(settings.chroma_persist_directory) == temp_dir
                assert isinstance(settings.backup_directory, Path)

    def test_boolean_settings(self):
        """Test boolean setting parsing."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
        ]

        for str_value, expected_bool in test_cases:
            test_env = {
                "REPORTPORTAL_URL": "https://test.com",
                "REPORTPORTAL_API_TOKEN": "test_token",
                "DEV_MODE": str_value,
                "ENABLE_DOCS": str_value,
                "API_DEBUG": str_value,
            }

            with patch.dict(os.environ, test_env):
                settings = Settings()

                assert settings.dev_mode is expected_bool
                assert settings.enable_docs is expected_bool
                assert settings.api_debug is expected_bool

    def test_integer_settings(self):
        """Test integer setting parsing."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "API_PORT": "9999",
            "SYNC_BATCH_SIZE": "200",
            "LLM_MAX_TOKENS": "4000",
            "WORKERS": "8",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()

            assert settings.api_port == 9999
            assert settings.sync_batch_size == 200
            assert settings.llm_max_tokens == 4000
            assert settings.workers == 8

    def test_float_settings(self):
        """Test float setting parsing."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "LLM_TEMPERATURE": "0.5",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()

            assert settings.llm_temperature == 0.5

    def test_optional_settings(self):
        """Test optional settings handling."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "OPENAI_API_KEY": "test_openai_key",
            "SLACK_BOT_TOKEN": "test_slack_token",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()

            assert settings.openai_api_key == "test_openai_key"
            assert settings.slack_bot_token == "test_slack_token"
            assert settings.anthropic_api_key is None  # Not set
            assert settings.reportportal_project is None  # Not set


class TestSettingsProperties:
    """Test Settings properties and methods."""

    def test_reportportal_base_url(self):
        """Test reportportal_base_url property."""
        test_env = {
            "REPORTPORTAL_URL": "https://my-reportportal.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()

            assert settings.reportportal_base_url == "https://my-reportportal.com/api"

    def test_cors_origins_list_wildcard(self):
        """Test CORS origins list with wildcard."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "API_CORS_ORIGINS": "*",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()

            assert settings.cors_origins_list == ["*"]

    def test_cors_origins_list_multiple(self):
        """Test CORS origins list with multiple origins."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "API_CORS_ORIGINS": "https://app1.com,https://app2.com, https://app3.com",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()

            expected = ["https://app1.com", "https://app2.com", "https://app3.com"]
            assert settings.cors_origins_list == expected

    def test_effective_log_level(self):
        """Test effective log level property."""
        # Test with API-specific log level
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "LOG_LEVEL": "WARNING",
            "API_LOG_LEVEL": "DEBUG",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()

            assert settings.effective_log_level == "DEBUG"
            assert settings.log_level == "WARNING"

    def test_effective_log_format(self):
        """Test effective log format property."""
        # Test with API-specific log format
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "LOG_FORMAT": "console",
            "API_LOG_FORMAT": "json",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()

            assert settings.effective_log_format == "json"
            assert settings.log_format == "console"

    def test_is_development(self):
        """Test is_development method."""
        # Test development mode via dev_mode
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "DEV_MODE": "true",
            "API_DEBUG": "false",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()
            assert settings.is_development() is True

        # Test development mode via api_debug
        test_env["DEV_MODE"] = "false"
        test_env["API_DEBUG"] = "true"

        with patch.dict(os.environ, test_env):
            settings = Settings()
            assert settings.is_development() is True

        # Test production mode
        test_env["DEV_MODE"] = "false"
        test_env["API_DEBUG"] = "false"

        with patch.dict(os.environ, test_env):
            settings = Settings()
            assert settings.is_development() is False

    def test_is_production(self):
        """Test is_production method."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "DEV_MODE": "false",
            "API_DEBUG": "false",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()
            assert settings.is_production() is True

        # Test with development mode
        test_env["DEV_MODE"] = "true"

        with patch.dict(os.environ, test_env):
            settings = Settings()
            assert settings.is_production() is False


class TestSettingsConfigMethods:
    """Test Settings configuration helper methods."""

    def test_get_openai_config(self):
        """Test get_openai_config method."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "OPENAI_API_KEY": "test_openai_key",
            "OPENAI_MODEL": "gpt-4",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "LLM_TEMPERATURE": "0.8",
            "LLM_MAX_TOKENS": "3000",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()
            config = settings.get_openai_config()

            assert config["api_key"] == "test_openai_key"
            assert config["model"] == "gpt-4"
            assert config["base_url"] == "https://api.openai.com/v1"
            assert config["temperature"] == 0.8
            assert config["max_tokens"] == 3000

    def test_get_anthropic_config(self):
        """Test get_anthropic_config method."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "ANTHROPIC_API_KEY": "test_anthropic_key",
            "ANTHROPIC_MODEL": "claude-3-opus",
            "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
            "LLM_TEMPERATURE": "0.6",
            "LLM_MAX_TOKENS": "2500",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()
            config = settings.get_anthropic_config()

            assert config["api_key"] == "test_anthropic_key"
            assert config["model"] == "claude-3-opus"
            assert config["base_url"] == "https://api.anthropic.com"
            assert config["temperature"] == 0.6
            assert config["max_tokens"] == 2500

    def test_get_ollama_config(self):
        """Test get_ollama_config method."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_MODEL": "llama3",
            "LLM_TEMPERATURE": "0.7",
            "LLM_MAX_TOKENS": "2000",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()
            config = settings.get_ollama_config()

            assert config["base_url"] == "http://localhost:11434"
            assert config["model"] == "llama3"
            assert config["temperature"] == 0.7
            assert config["max_tokens"] == 2000

    def test_get_slack_config(self):
        """Test get_slack_config method."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_SIGNING_SECRET": "test_secret",
            "SLACK_DEFAULT_CHANNEL": "#test-insights",
        }

        with patch.dict(os.environ, test_env):
            settings = Settings()
            config = settings.get_slack_config()

            assert config["bot_token"] == "xoxb-test-token"
            assert config["signing_secret"] == "test_secret"
            assert config["default_channel"] == "#test-insights"


class TestSettingsValidation:
    """Test Settings validation and error handling."""

    def test_missing_required_settings(self):
        """Test behavior with missing required settings."""
        # Clear environment to test missing required settings
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):  # Should raise validation error
                Settings()

    def test_invalid_port_number(self):
        """Test invalid port number handling."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "API_PORT": "invalid_port",
        }

        with patch.dict(os.environ, test_env):
            with pytest.raises(Exception):  # Should raise validation error
                Settings()

    def test_invalid_boolean_values(self):
        """Test invalid boolean value handling."""
        test_env = {
            "REPORTPORTAL_URL": "https://test.com",
            "REPORTPORTAL_API_TOKEN": "test_token",
            "DEV_MODE": "maybe",  # Invalid boolean value
        }

        with patch.dict(os.environ, test_env):
            with pytest.raises(Exception):  # Should raise validation error
                Settings()

    def test_env_file_loading(self):
        """Test .env file loading."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("REPORTPORTAL_URL=https://from-file.com\n")
            f.write("REPORTPORTAL_API_TOKEN=file_token\n")
            f.write("API_HOST=file_host\n")
            env_file_path = f.name

        try:
            # Create settings with custom env file
            settings = Settings(_env_file=env_file_path)

            assert settings.reportportal_url == "https://from-file.com"
            assert settings.reportportal_api_token == "file_token"
            assert settings.api_host == "file_host"
        finally:
            Path(env_file_path).unlink()  # Clean up temp file
