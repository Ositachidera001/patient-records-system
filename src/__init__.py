"""
src package marker. 

This file is intentionally empty of logic. Its only job is to tell
python "src/ is a package", so that test_models.py (which lives at the 
project root) can do 'from src.models import patient'.

Everything that actually runs the app lives in main.py and is launched
with 'python src/main.py', which is a different import mode (script
mode) that's why the othermodules inside src/ use flat imports like 
'from config import WIDTH' instead of 'from .config import WIDTH'.
"""