"""
api.extensions - Flask extensions
---------------------------------

This module defines and configures Flask extensions used by the application.
It provides a centralized place to manage extensions like rate limiting.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
