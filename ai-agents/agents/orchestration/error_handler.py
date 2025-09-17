"""
Production-ready error handling for campaign orchestration
"""
import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"        # Log and continue
    MEDIUM = "medium"  # Alert but continue
    HIGH = "high"      # Alert and may need intervention
    CRITICAL = "critical"  # Stop execution

class ErrorCategory(Enum):
    """Error categories for better tracking"""
    DATABASE = "database"
    API = "api"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    PERMISSION = "permission"
    UNKNOWN = "unknown"

class CampaignErrorHandler:
    """Handles errors in campaign orchestration with proper logging and recovery"""

    def __init__(self):
        self.error_log = []
        self.max_retries = 3
        self.retry_delays = [1, 5, 15]  # seconds

    def handle_error(self,
                    error: Exception,
                    context: dict[str, Any],
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.UNKNOWN) -> dict[str, Any]:
        """
        Handle an error with proper logging and recovery strategy

        Args:
            error: The exception that occurred
            context: Context about where/when the error occurred
            severity: How severe the error is
            category: What type of error it is

        Returns:
            Error response with recovery suggestions
        """
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{category.value}"

        error_details = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "severity": severity.value,
            "category": category.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }

        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"[{error_id}] {error}", extra=error_details)
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"[{error_id}] {error}", extra=error_details)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"[{error_id}] {error}", extra=error_details)
        else:
            logger.info(f"[{error_id}] {error}", extra=error_details)

        # Store in error log
        self.error_log.append(error_details)

        # Determine recovery strategy
        recovery_strategy = self._determine_recovery(error, category)

        return {
            "success": False,
            "error_id": error_id,
            "error": str(error),
            "category": category.value,
            "severity": severity.value,
            "recovery_strategy": recovery_strategy,
            "user_message": self._get_user_message(error, category)
        }

    def _determine_recovery(self, error: Exception, category: ErrorCategory) -> dict[str, Any]:
        """Determine the best recovery strategy based on error type"""

        if category == ErrorCategory.DATABASE:
            if "violates row-level security policy" in str(error):
                return {
                    "action": "fix_permissions",
                    "suggestion": "Database permissions need to be updated. Contact admin.",
                    "can_retry": False
                }
            elif "connection" in str(error).lower():
                return {
                    "action": "retry_with_backoff",
                    "suggestion": "Database connection issue. Will retry.",
                    "can_retry": True,
                    "retry_after": 5
                }

        elif category == ErrorCategory.RATE_LIMIT:
            return {
                "action": "wait_and_retry",
                "suggestion": "Rate limit reached. Wait before retrying.",
                "can_retry": True,
                "retry_after": 60
            }

        elif category == ErrorCategory.VALIDATION:
            return {
                "action": "fix_input",
                "suggestion": "Invalid input data. Check and correct the request.",
                "can_retry": False
            }

        elif category == ErrorCategory.TIMEOUT:
            return {
                "action": "retry_partial",
                "suggestion": "Operation timed out. May retry with smaller batch.",
                "can_retry": True,
                "retry_after": 10
            }

        # Default recovery
        return {
            "action": "log_and_continue",
            "suggestion": "Error logged. Operation may continue with degraded functionality.",
            "can_retry": False
        }

    def _get_user_message(self, error: Exception, category: ErrorCategory) -> str:
        """Get a user-friendly error message"""

        if category == ErrorCategory.PERMISSION:
            return "Permission denied. Please check your access rights."
        elif category == ErrorCategory.DATABASE:
            if "row-level security" in str(error):
                return "Database security policy is blocking this operation. Please contact support."
            return "Database error occurred. Please try again later."
        elif category == ErrorCategory.VALIDATION:
            return f"Invalid input: {error!s}"
        elif category == ErrorCategory.TIMEOUT:
            return "The operation took too long. Please try again with fewer items."
        elif category == ErrorCategory.RATE_LIMIT:
            return "Too many requests. Please wait a moment before trying again."
        else:
            return "An unexpected error occurred. Please try again or contact support."

    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Automatically categorize an error based on its type and message"""
        error_str = str(error).lower()

        # Database errors
        if any(db_term in error_str for db_term in ["database", "postgrest", "supabase", "row-level security", "foreign key"]):
            return ErrorCategory.DATABASE

        # Permission errors
        if any(perm_term in error_str for perm_term in ["permission", "unauthorized", "forbidden", "invalid api key"]):
            return ErrorCategory.PERMISSION

        # Validation errors
        if any(val_term in error_str for val_term in ["validation", "invalid", "missing required", "type error"]):
            return ErrorCategory.VALIDATION

        # Timeout errors
        if any(time_term in error_str for time_term in ["timeout", "timed out", "deadline"]):
            return ErrorCategory.TIMEOUT

        # Rate limit errors
        if any(rate_term in error_str for rate_term in ["rate limit", "too many requests", "429"]):
            return ErrorCategory.RATE_LIMIT

        # API errors
        if any(api_term in error_str for api_term in ["api", "endpoint", "http"]):
            return ErrorCategory.API

        return ErrorCategory.UNKNOWN

    def get_error_summary(self) -> dict[str, Any]:
        """Get a summary of all errors in this session"""
        if not self.error_log:
            return {"total_errors": 0, "by_category": {}, "by_severity": {}}

        by_category = {}
        by_severity = {}

        for error in self.error_log:
            # Count by category
            cat = error["category"]
            by_category[cat] = by_category.get(cat, 0) + 1

            # Count by severity
            sev = error["severity"]
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "total_errors": len(self.error_log),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": self.error_log[-5:]  # Last 5 errors
        }

# Global error handler instance
error_handler = CampaignErrorHandler()
