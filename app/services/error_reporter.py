"""
Automatic error reporting service for GitHub Issues.

This module categorizes errors and automatically reports bugs to GitHub
while keeping user configuration errors local.
"""

import requests
import logging
import traceback
import os
import platform
import sys
from typing import Dict, Optional
from datetime import datetime
from app.models import ErrorLog, get_session

logger = logging.getLogger(__name__)


class ErrorReporter:
    """
    Handles error categorization and automatic reporting to GitHub Issues.
    """

    # Known user/config error patterns
    USER_ERROR_PATTERNS = [
        'ConnectionError',
        'ConnectionRefusedError',
        'Timeout',
        'TimeoutError',
        'PermissionError',
        'FileNotFoundError',
        'ConfigurationError',
        'ValidationError',
        'DNSLookupError',
        'NetworkUnreachable',
    ]

    def __init__(self, db_session=None, github_token: str = None, repo: str = None):
        """
        Initialize the error reporter.

        Args:
            db_session: SQLAlchemy session
            github_token: GitHub personal access token
            repo: GitHub repository (format: "owner/repo")
        """
        self.session = db_session or get_session()
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.repo = repo or os.getenv('GITHUB_REPO', 'builderOfTheWorlds/denon_avr_x2300w_webGUI')
        self.auto_report_enabled = os.getenv('AUTO_REPORT_ERRORS', 'true').lower() == 'true'

    def handle_error(
        self,
        error: Exception,
        context: Dict = None,
        request_path: str = None,
        user_agent: str = None
    ) -> Optional[int]:
        """
        Handle an error by categorizing and optionally reporting it.

        Args:
            error: The exception that occurred
            context: Additional context about the error
            request_path: API request path if applicable
            user_agent: User agent string if applicable

        Returns:
            GitHub issue number if reported, None otherwise
        """
        context = context or {}

        try:
            # Get error details
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = traceback.format_exc()

            # Categorize the error
            category = self._categorize_error(error_type, error_message, stack_trace)

            logger.debug(f"Error categorized as: {category}")

            # Log to database
            error_log = ErrorLog(
                error_type=error_type,
                error_category=category,
                error_message=error_message,
                stack_trace=stack_trace,
                request_path=request_path,
                user_agent=user_agent
            )

            self.session.add(error_log)
            self.session.commit()

            # Report bugs automatically
            if category == 'bug' and self.auto_report_enabled:
                issue_number = self._report_to_github(
                    error_type=error_type,
                    error_message=error_message,
                    stack_trace=stack_trace,
                    context=context
                )

                if issue_number:
                    error_log.reported_to_github = True
                    error_log.github_issue_number = issue_number
                    self.session.commit()
                    return issue_number

            return None

        except Exception as e:
            logger.error(f"Error in error reporter: {str(e)}", exc_info=True)
            return None

    def _categorize_error(self, error_type: str, error_message: str, stack_trace: str) -> str:
        """
        Categorize an error as user error or bug.

        Args:
            error_type: Type of exception
            error_message: Error message
            stack_trace: Full stack trace

        Returns:
            'user_error', 'bug', or 'unknown'
        """
        # Check if it matches known user error patterns
        for pattern in self.USER_ERROR_PATTERNS:
            if pattern.lower() in error_type.lower() or pattern.lower() in error_message.lower():
                return 'user_error'

        # Check for common configuration issues
        config_keywords = ['config', 'permission', 'not found', 'cannot connect', 'unreachable']
        if any(keyword in error_message.lower() for keyword in config_keywords):
            return 'user_error'

        # If it's a processing error in our code, it's likely a bug
        if 'app/' in stack_trace or 'lib/' in stack_trace:
            return 'bug'

        return 'unknown'

    def _report_to_github(
        self,
        error_type: str,
        error_message: str,
        stack_trace: str,
        context: Dict
    ) -> Optional[int]:
        """
        Create a GitHub issue for the error.

        Args:
            error_type: Type of exception
            error_message: Error message
            stack_trace: Full stack trace
            context: Additional context

        Returns:
            GitHub issue number if created, None otherwise
        """
        if not self.github_token:
            logger.warning("GitHub token not configured, cannot auto-report errors")
            return None

        try:
            # Check if similar issue already exists
            existing_issue = self._find_existing_issue(error_type, error_message)
            if existing_issue:
                logger.info(f"Similar issue already exists: #{existing_issue}")
                return existing_issue

            # Create issue title
            title = f"[Auto-Report] {error_type}: {error_message[:80]}"

            # Create issue body
            body = self._format_issue_body(error_type, error_message, stack_trace, context)

            # Create the issue
            url = f"https://api.github.com/repos/{self.repo}/issues"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            payload = {
                'title': title,
                'body': body,
                'labels': ['bug', 'auto-reported']
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 201:
                issue_data = response.json()
                issue_number = issue_data['number']
                logger.info(f"Created GitHub issue #{issue_number}")
                return issue_number
            else:
                logger.error(f"Failed to create GitHub issue: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error reporting to GitHub: {str(e)}", exc_info=True)
            return None

    def _find_existing_issue(self, error_type: str, error_message: str) -> Optional[int]:
        """
        Search for existing issues with similar errors.

        Args:
            error_type: Type of exception
            error_message: Error message

        Returns:
            Issue number if found, None otherwise
        """
        try:
            # Search for open issues with same error type
            url = f"https://api.github.com/repos/{self.repo}/issues"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            params = {
                'state': 'open',
                'labels': 'auto-reported',
                'per_page': 30
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                issues = response.json()

                # Look for similar error type in title
                for issue in issues:
                    if error_type in issue['title']:
                        return issue['number']

        except Exception as e:
            logger.debug(f"Error searching for existing issues: {str(e)}")

        return None

    def _format_issue_body(
        self,
        error_type: str,
        error_message: str,
        stack_trace: str,
        context: Dict
    ) -> str:
        """
        Format the GitHub issue body.

        Args:
            error_type: Type of exception
            error_message: Error message
            stack_trace: Full stack trace
            context: Additional context

        Returns:
            Formatted issue body
        """
        # Get environment info
        env_info = self._get_environment_info()

        # Sanitize stack trace (remove sensitive info)
        sanitized_trace = self._sanitize_stack_trace(stack_trace)

        body = f"""## Auto-Reported Error

**Error Type:** `{error_type}`

**Error Message:**
```
{error_message}
```

### Stack Trace
```python
{sanitized_trace}
```

### Environment
{env_info}

### Additional Context
```json
{context}
```

---
*This issue was automatically created by the Sugartalking error reporting system.*
*Timestamp: {datetime.utcnow().isoformat()}Z*
"""

        return body

    def _get_environment_info(self) -> str:
        """
        Get environment information for the issue report.

        Returns:
            Formatted environment info
        """
        try:
            info = f"""
- **Platform:** {platform.system()} {platform.release()}
- **Python Version:** {sys.version.split()[0]}
- **Architecture:** {platform.machine()}
"""
            return info
        except:
            return "Environment info not available"

    def _sanitize_stack_trace(self, stack_trace: str) -> str:
        """
        Remove sensitive information from stack trace.

        Args:
            stack_trace: Original stack trace

        Returns:
            Sanitized stack trace
        """
        # Remove IP addresses
        import re
        sanitized = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '***.***.***.**', stack_trace)

        # Remove file paths (keep only relative paths)
        sanitized = re.sub(r'/home/[^/]+/', '/home/user/', sanitized)
        sanitized = re.sub(r'C:\\Users\\[^\\]+\\', 'C:\\Users\\user\\', sanitized)

        # Limit length
        if len(sanitized) > 5000:
            sanitized = sanitized[:5000] + "\n\n... (truncated)"

        return sanitized

    def get_error_stats(self) -> Dict:
        """
        Get statistics about errors.

        Returns:
            Dictionary with error statistics
        """
        try:
            from sqlalchemy import func

            total_errors = self.session.query(ErrorLog).count()
            user_errors = self.session.query(ErrorLog).filter_by(error_category='user_error').count()
            bugs = self.session.query(ErrorLog).filter_by(error_category='bug').count()
            reported = self.session.query(ErrorLog).filter_by(reported_to_github=True).count()

            return {
                'total_errors': total_errors,
                'user_errors': user_errors,
                'bugs': bugs,
                'reported_to_github': reported,
                'unreported_bugs': bugs - reported
            }

        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}", exc_info=True)
            return {}
