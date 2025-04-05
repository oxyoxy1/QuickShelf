from setuptools import setup

APP = ['quickshelf.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['sklearn', 'pandas', 'matplotlib'],
    'iconfile': 'quickshelf.icns'  # Optional: add an icon file
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)