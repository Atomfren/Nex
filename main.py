"""NexoraLauncher - Main entry point."""

import sys
from pathlib import Path

# Добавляем корень проекта в PATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from frontend.main import main

if __name__ == "__main__":
    main()
