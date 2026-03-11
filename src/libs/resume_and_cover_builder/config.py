"""
Configuration for the resume and cover letter builder.

GlobalConfig is initialised once by ResumeFacade and read by every downstream
module.  Mutations after construction are discouraged — pass a fresh instance
instead of mutating the module-level ``global_config``.
"""

from pathlib import Path

from pydantic import BaseModel

_DEFAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" />
    <style>
        $style_css
    </style>
</head>
<body>
$body
</body>
</html>
"""


class GlobalConfig(BaseModel):
    STYLES_DIRECTORY: Path | None = None
    LOG_OUTPUT_FILE_PATH: Path | None = None
    API_KEY: str | None = None
    html_template: str = _DEFAULT_HTML_TEMPLATE


global_config = GlobalConfig()
