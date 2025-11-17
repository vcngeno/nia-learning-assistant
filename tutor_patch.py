# Add this import at line 6 (after import os)
import json

# Add this method after __init__ (around line 30)
    def set_tools(self, tools, available_functions):
        """Set the tools and functions for function calling"""
        self.tools = tools
        self.available_functions = available_functions
