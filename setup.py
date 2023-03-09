"""Setup.py for LexiScore."""
from setuptools import setup, find_packages
# List of requirements
requirements = []  # This could be retrieved from requirements.txt
# Package (minimal) configuration
setup(
    name="LexiScore",
    version="0.1.0",
    description="A FastAPI webservices for a probability of a word belonging to a certain language",
    packages=find_packages(),  # __init__.py folders search
    install_requires=requirements
)
