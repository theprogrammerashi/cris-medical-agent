import os
import logging

def setup_logging():
    """Configures standard logging for the app."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def ensure_directories_exist():
    """Creates necessary data folders if they don't exist."""
    folders = [
        "data/knowledge_base",
        "data/uploads"
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def format_agent_output(raw_output):
    """Cleans up the markdown output from agents for better display."""
    if not raw_output:
        return ""
    return str(raw_output).strip()