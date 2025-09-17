"""
Intelligent Messaging Agent Package
Business Critical: GPT-4o powered security and scope change detection
"""

from .agent import (
    # Main processing function
    process_intelligent_message,
    
    # Core classes that exist
    GPT5SecurityAnalyzer,
    
    # State and types
    MessageType,
    AgentAction,
    SecurityThreat,
    ProjectScopeChange
)

from .scope_change_handler import (
    ScopeChangeHandler,
    handle_scope_changes
)

__all__ = [
    # Main function
    'process_intelligent_message',
    
    # Core classes
    'GPT5SecurityAnalyzer',
    
    # Types
    'MessageType',
    'AgentAction',
    'SecurityThreat',
    'ProjectScopeChange',
    
    # Scope handling
    'ScopeChangeHandler',
    'handle_scope_changes'
]