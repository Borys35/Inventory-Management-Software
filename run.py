import sys
import os

# Dodanie folderu backend do ścieżek systemowych (standardowa praktyka)
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import app

if __name__ == '__main__':
    app.run(debug=True)