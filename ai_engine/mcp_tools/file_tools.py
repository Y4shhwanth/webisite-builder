"""
MCP Tools for file operations (Read, Write, Edit)
"""
import os
from typing import Dict, Any, Optional
from logging_config import logger
from config import settings


async def read_file(file_path: str) -> Dict[str, Any]:
    """
    Read content from a file.

    Args:
        file_path: Path to the file to read

    Returns:
        File content and metadata
    """
    try:
        # Ensure file is within allowed directory
        full_path = os.path.join(settings.GENERATED_WEBSITES_DIR, file_path)

        if not os.path.exists(full_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"Read file: {file_path}")

        return {
            "success": True,
            "file_path": file_path,
            "content": content,
            "size": len(content)
        }

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    Write content to a file (create or overwrite).

    Args:
        file_path: Path to the file to write
        content: Content to write

    Returns:
        Success status and metadata
    """
    try:
        # Ensure directory exists
        os.makedirs(settings.GENERATED_WEBSITES_DIR, exist_ok=True)

        full_path = os.path.join(settings.GENERATED_WEBSITES_DIR, file_path)

        # Create parent directories if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Wrote file: {file_path} ({len(content)} bytes)")

        return {
            "success": True,
            "file_path": file_path,
            "size": len(content)
        }

    except Exception as e:
        logger.error(f"Error writing file {file_path}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def edit_file(
    file_path: str,
    old_string: str,
    new_string: str
) -> Dict[str, Any]:
    """
    Edit a file by replacing old_string with new_string.

    Args:
        file_path: Path to the file to edit
        old_string: String to find and replace
        new_string: Replacement string

    Returns:
        Success status and metadata
    """
    try:
        # Read current content
        read_result = await read_file(file_path)
        if not read_result.get("success"):
            return read_result

        content = read_result["content"]

        # Check if old_string exists
        if old_string not in content:
            return {
                "success": False,
                "error": f"String not found in file: {old_string[:100]}..."
            }

        # Replace content
        new_content = content.replace(old_string, new_string, 1)

        # Write back
        write_result = await write_file(file_path, new_content)

        if write_result.get("success"):
            logger.info(f"Edited file: {file_path}")

        return write_result

    except Exception as e:
        logger.error(f"Error editing file {file_path}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# Tool definitions for Claude Agents SDK
FILE_TOOLS = {
    "read_file": {
        "name": "Read",
        "description": "Read content from a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["file_path"]
        },
        "function": read_file
    },
    "write_file": {
        "name": "Write",
        "description": "Write content to a file (create or overwrite)",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        },
        "function": write_file
    },
    "edit_file": {
        "name": "Edit",
        "description": "Edit a file by replacing a string",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to edit"
                },
                "old_string": {
                    "type": "string",
                    "description": "String to find and replace"
                },
                "new_string": {
                    "type": "string",
                    "description": "Replacement string"
                }
            },
            "required": ["file_path", "old_string", "new_string"]
        },
        "function": edit_file
    }
}
