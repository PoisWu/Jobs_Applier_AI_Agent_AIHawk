"""Utility functions for the Resume and Cover Letter Builder service."""

import textwrap


def preprocess_template_string(template: str) -> str:
    """Remove leading whitespace and indentation from a prompt template."""
    return textwrap.dedent(template)
