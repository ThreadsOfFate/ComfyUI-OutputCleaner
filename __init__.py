from .output_cleaner import OutputCleaner

NODE_CLASS_MAPPINGS = {
    "OutputCleaner": OutputCleaner,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OutputCleaner": "Output Cleaner 🗑️",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
