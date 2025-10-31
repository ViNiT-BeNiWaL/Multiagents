"""
Security module for validating and sanitizing agent operations
"""
import re
from typing import List, Dict, Any
from enum import Enum


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityValidator:
    """Validates and sanitizes agent operations for security"""

    FORBIDDEN_PATTERNS = [
        r'rm\s+-rf\s+/',
        r'dd\s+if=',
        r':(){ :|:& };:',  # Fork bomb
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
    ]

    ALLOWED_FILE_EXTENSIONS = [
        '.txt', '.md', '.py', '.json', '.yaml', '.yml',
        '.csv', '.log', '.conf', '.ini'
    ]

    def __init__(self):
        self.security_log: List[Dict[str, Any]] = []

    def validate_command(self, command: str, level: SecurityLevel = SecurityLevel.MEDIUM) -> tuple[bool, str]:
        """
        Validate a command for security risks

        Args:
            command: Command to validate
            level: Security level to enforce

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                reason = f"Forbidden pattern detected: {pattern}"
                self._log_security_event("command_blocked", command, reason)
                return False, reason

        # Check for suspicious characters at high security
        if level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            suspicious_chars = ['&', '|', ';', '>', '<', '`', '$']
            if any(char in command for char in suspicious_chars):
                reason = "Suspicious shell characters detected"
                self._log_security_event("command_blocked", command, reason)
                return False, reason

        return True, "Command validated"

    def validate_file_path(self, file_path: str) -> tuple[bool, str]:
        """
        Validate a file path for security

        Args:
            file_path: Path to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check for path traversal
        if '..' in file_path:
            reason = "Path traversal detected"
            self._log_security_event("path_blocked", file_path, reason)
            return False, reason

        # Check for absolute paths outside allowed directories
        if file_path.startswith('/etc') or file_path.startswith('/sys'):
            reason = "Access to system directories not allowed"
            self._log_security_event("path_blocked", file_path, reason)
            return False, reason

        return True, "Path validated"

    def sanitize_input(self, user_input: str) -> str:
        """
        Sanitize user input

        Args:
            user_input: Input to sanitize

        Returns:
            Sanitized input
        """
        # Remove null bytes
        sanitized = user_input.replace('\x00', '')

        # Remove control characters except newlines and tabs
        sanitized = ''.join(char for char in sanitized if char in '\n\t' or ord(char) >= 32)

        return sanitized

    def _log_security_event(self, event_type: str, content: str, reason: str):
        """Log security events"""
        self.security_log.append({
            'type': event_type,
            'content': content[:100],  # Truncate for logging
            'reason': reason
        })

    def get_security_report(self) -> List[Dict[str, Any]]:
        """Get security event log"""
        return self.security_log.copy()