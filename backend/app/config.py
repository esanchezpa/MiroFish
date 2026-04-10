"""
Configuration management
Loads config from the project root .env file
"""

import os
from dotenv import load_dotenv

# Load .env from project root (relative to backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    load_dotenv(override=True)


class Config:
    """Flask configuration class"""
    
    # Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mirofish-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # JSON config - disable ASCII escaping for direct Unicode output
    JSON_AS_ASCII = False
    
    # LLM config (OpenAI-compatible format)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    # Zep config
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')
    
    # File upload config
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
    
    # --- Text processing config (v0.2: optimized for large PDF corpora) ---
    # Default profile: free_tier_large_corpus
    # For 2.8M chars: ~727 chunks, ~61 batches (vs 2860 batches with old defaults)
    DEFAULT_CHUNK_SIZE = 4000           # was 500 — larger chunks = fewer episodes
    DEFAULT_CHUNK_OVERLAP = 120         # was 50
    DEFAULT_BATCH_SIZE = 12             # was 3 (hardcoded) — fewer API calls, same data
    DEFAULT_BOUNDARY_MIN_FILL_RATIO = 0.80   # min fill before accepting a boundary cut
    DEFAULT_MIN_CHUNK_CHARS = 2200      # reject micro-chunks below this size
    DEFAULT_EPISODE_PACK_SIZE = 1       # episodes per Zep episode object
    DEFAULT_WARN_EPISODE_THRESHOLD = 700     # yellow warning at this episode count
    DEFAULT_HARD_STOP_EPISODE_THRESHOLD = 850  # red block: will exceed free Zep quota
    
    # OASIS simulation config
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    
    # OASIS platform actions
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]
    
    # Report Agent config
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY not configured")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY not configured")
        return errors
