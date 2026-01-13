import warnings
import pytest
import os

# Filter warnings immediately upon import
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Specific filters for stubborn libraries
warnings.filterwarnings("ignore", module="slowapi")
warnings.filterwarnings("ignore", module="langsmith")
warnings.filterwarnings("ignore", module="google.genai")
