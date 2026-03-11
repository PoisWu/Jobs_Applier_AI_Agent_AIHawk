# In this file, you can set the configurations of the app.

from src.utils.constants import ERROR

# config related to logging must have prefix LOG_
LOG_LEVEL = "DEBUG"
LOG_SELENIUM_LEVEL = ERROR
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

MINIMUM_WAIT_TIME_IN_SECONDS = 60

JOB_APPLICATIONS_DIR = "job_applications"
JOB_SUITABILITY_SCORE = 7

JOB_MAX_APPLICATIONS = 5
JOB_MIN_APPLICATIONS = 1

LLM_MODEL_TYPE = "openai"
LLM_MODEL = "gpt-4o-mini"
# Only required for OLLAMA models
LLM_API_URL = ""

# LLM tuning
LLM_TEMPERATURE = 0.4

# Token pricing (for cost tracking)
PROMPT_PRICE_PER_TOKEN = 0.00000015
COMPLETION_PRICE_PER_TOKEN = 0.0000006

# Retry configuration
MAX_LLM_RETRIES = 15
BASE_RETRY_DELAY = 10

# Output
OUTPUT_DIR = "data_folder/output"
HASH_PREFIX_LENGTH = 10
