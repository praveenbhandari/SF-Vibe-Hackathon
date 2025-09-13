#!/usr/bin/env python3
"""
Canvas API Configuration Management

Secure configuration and token storage for Canvas API client.
Supports environment variables, config files, and secure token handling.
"""

import os
import json
import keyring
import getpass
from pathlib import Path
from typing import Dict, Optional, Any
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class CanvasConfig:
    """
    Secure configuration management for Canvas API
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or os.path.expanduser('~/.canvas_config.json')
        self.keyring_service = 'canvas-api-client'
        self.keyring_username = 'api-token'
        
        # Load environment variables from .env file if it exists
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from multiple sources in priority order:
        1. Environment variables
        2. Configuration file
        3. System keyring
        4. Default values
        """
        config = {
            'base_url': None,
            'api_token': None,
            'rate_limit': 10,
            'max_retries': 3,
            'timeout': 30,
            'debug_logging': False
        }
        
        # 1. Load from environment variables
        config.update(self._load_from_env())
        
        # 2. Load from config file
        file_config = self._load_from_file()
        if file_config:
            config.update(file_config)
        
        # 3. Load API token from keyring if not found elsewhere
        if not config.get('api_token'):
            keyring_token = self._load_token_from_keyring()
            if keyring_token:
                config['api_token'] = keyring_token
        
        return config
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_config = {}
        
        if os.getenv('CANVAS_BASE_URL'):
            env_config['base_url'] = os.getenv('CANVAS_BASE_URL')
        
        if os.getenv('CANVAS_API_TOKEN'):
            env_config['api_token'] = os.getenv('CANVAS_API_TOKEN')
        
        if os.getenv('RATE_LIMIT'):
            try:
                env_config['rate_limit'] = int(os.getenv('RATE_LIMIT'))
            except ValueError:
                logger.warning("Invalid RATE_LIMIT value in environment")
        
        if os.getenv('DEBUG_LOGGING'):
            env_config['debug_logging'] = os.getenv('DEBUG_LOGGING').lower() in ('true', '1', 'yes')
        
        return env_config
    
    def _load_from_file(self) -> Optional[Dict[str, Any]]:
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    logger.debug(f"Loaded configuration from {self.config_file}")
                    return file_config
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        return None
    
    def _load_token_from_keyring(self) -> Optional[str]:
        """Load API token from system keyring"""
        try:
            token = keyring.get_password(self.keyring_service, self.keyring_username)
            if token:
                logger.debug("Loaded API token from system keyring")
            return token
        except Exception as e:
            logger.debug(f"Failed to load token from keyring: {e}")
            return None
    
    def save_config(self, base_url: str = None, api_token: str = None, 
                   use_keyring: bool = True, **kwargs) -> bool:
        """
        Save configuration to file and optionally store token in keyring
        
        Args:
            base_url: Canvas base URL
            api_token: Canvas API token
            use_keyring: Whether to store token in system keyring
            **kwargs: Additional configuration options
        
        Returns:
            bool: True if saved successfully
        """
        try:
            # Update current config
            if base_url:
                self.config['base_url'] = base_url
            if api_token:
                self.config['api_token'] = api_token
            
            # Update additional options
            self.config.update(kwargs)
            
            # Prepare config for file (exclude sensitive data if using keyring)
            file_config = self.config.copy()
            
            if use_keyring and api_token:
                # Store token in keyring
                self._save_token_to_keyring(api_token)
                # Remove token from file config
                file_config.pop('api_token', None)
                logger.info("API token stored securely in system keyring")
            
            # Save to file
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(file_config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def _save_token_to_keyring(self, token: str) -> bool:
        """Save API token to system keyring"""
        try:
            keyring.set_password(self.keyring_service, self.keyring_username, token)
            return True
        except Exception as e:
            logger.warning(f"Failed to save token to keyring: {e}")
            return False
    
    def setup_interactive(self) -> bool:
        """
        Interactive setup for Canvas API configuration
        
        Returns:
            bool: True if setup completed successfully
        """
        print("\n=== Canvas API Configuration Setup ===")
        print("This will help you configure your Canvas API connection.\n")
        
        # Get base URL
        current_url = self.config.get('base_url', '')
        if current_url:
            print(f"Current Canvas URL: {current_url}")
        
        base_url = input("Enter your Canvas base URL (e.g., https://your-school.instructure.com): ").strip()
        if not base_url:
            if not current_url:
                print("Base URL is required!")
                return False
            base_url = current_url
        
        # Get API token
        print("\nTo get your Canvas API token:")
        print("1. Log into Canvas")
        print("2. Go to Account → Settings → Approved Integrations")
        print("3. Click '+ New Access Token'")
        print("4. Generate and copy the token\n")
        
        api_token = getpass.getpass("Enter your Canvas API token (hidden): ").strip()
        if not api_token:
            print("API token is required!")
            return False
        
        # Ask about keyring storage
        use_keyring = input("Store API token securely in system keyring? (y/n) [y]: ").strip().lower()
        use_keyring = use_keyring != 'n'
        
        # Optional settings
        print("\n=== Optional Settings ===")
        rate_limit = input(f"Requests per second [{self.config.get('rate_limit', 10)}]: ").strip()
        if rate_limit:
            try:
                rate_limit = int(rate_limit)
            except ValueError:
                print("Invalid rate limit, using default")
                rate_limit = self.config.get('rate_limit', 10)
        else:
            rate_limit = self.config.get('rate_limit', 10)
        
        # Save configuration
        success = self.save_config(
            base_url=base_url,
            api_token=api_token,
            use_keyring=use_keyring,
            rate_limit=rate_limit
        )
        
        if success:
            print("\n✅ Configuration saved successfully!")
            print(f"Config file: {self.config_file}")
            if use_keyring:
                print("API token stored securely in system keyring")
        else:
            print("\n❌ Failed to save configuration")
        
        return success
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """
        Validate current configuration
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.config.get('base_url'):
            errors.append("Canvas base URL is not configured")
        
        if not self.config.get('api_token'):
            errors.append("Canvas API token is not configured")
        
        base_url = self.config.get('base_url', '')
        if base_url and not (base_url.startswith('http://') or base_url.startswith('https://')):
            errors.append("Base URL must start with http:// or https://")
        
        return len(errors) == 0, errors
    
    def clear_stored_token(self) -> bool:
        """
        Clear stored API token from keyring
        
        Returns:
            bool: True if cleared successfully
        """
        try:
            keyring.delete_password(self.keyring_service, self.keyring_username)
            logger.info("API token cleared from keyring")
            return True
        except Exception as e:
            logger.warning(f"Failed to clear token from keyring: {e}")
            return False
    
    def export_config(self, include_token: bool = False) -> Dict[str, Any]:
        """
        Export configuration for sharing or backup
        
        Args:
            include_token: Whether to include API token (not recommended)
        
        Returns:
            dict: Configuration data
        """
        config = self.config.copy()
        
        if not include_token:
            config.pop('api_token', None)
        
        return config


if __name__ == "__main__":
    # Interactive setup when run directly
    config = CanvasConfig()
    config.setup_interactive()