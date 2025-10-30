"""
arrive: A dynamical systems engine for GIS.
"""

from importlib.metadata import version

__version__ = version("arrive")

from .map_environment import show_on_basemap

__all__ = ["show_on_basemap", "__version__"]
