
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.main import app

if __name__ == "__main__":
    app.run()