"""
MaxIM Extensions & Capsule Integration Framework.
Allows external repositories, open source agents, and specialized tools
to be dynamically mounted into MaxIM without touching core codebase files.
"""
from extensions.extension_manager import extension_manager, ExtensionManager, ExtensionManifest

__all__ = ["extension_manager", "ExtensionManager", "ExtensionManifest"]
