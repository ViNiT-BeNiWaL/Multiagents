"""
File manager for handling file operations with security
"""
import os
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime


class FileManager:
    """Manages file operations with security checks"""

    def __init__(self, base_directory: str = "./workspace"):
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(exist_ok=True)
        self.file_history: List[Dict[str, Any]] = []

    def write_file(self, filepath: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Write content to a file

        Args:
            filepath: Path to file (relative to base directory)
            content: Content to write
            encoding: File encoding

        Returns:
            Dictionary with operation result
        """
        try:
            full_path = self._get_safe_path(filepath)

            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(full_path, 'w', encoding=encoding) as f:
                f.write(content)

            result = {
                'success': True,
                'filepath': str(full_path),
                'size': len(content),
                'timestamp': datetime.now().isoformat()
            }

            self._log_operation('write', filepath, result)
            return result

        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'filepath': filepath
            }
            self._log_operation('write', filepath, result)
            return result

    def read_file(self, filepath: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Read content from a file

        Args:
            filepath: Path to file (relative to base directory)
            encoding: File encoding

        Returns:
            Dictionary with file content or error
        """
        try:
            full_path = self._get_safe_path(filepath)

            if not full_path.exists():
                return {
                    'success': False,
                    'error': 'File not found',
                    'filepath': filepath
                }

            with open(full_path, 'r', encoding=encoding) as f:
                content = f.read()

            result = {
                'success': True,
                'content': content,
                'filepath': str(full_path),
                'size': len(content)
            }

            self._log_operation('read', filepath, {'success': True, 'size': len(content)})
            return result

        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'filepath': filepath
            }
            self._log_operation('read', filepath, result)
            return result

    def append_file(self, filepath: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Append content to a file

        Args:
            filepath: Path to file
            content: Content to append
            encoding: File encoding

        Returns:
            Dictionary with operation result
        """
        try:
            full_path = self._get_safe_path(filepath)
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, 'a', encoding=encoding) as f:
                f.write(content)

            result = {
                'success': True,
                'filepath': str(full_path),
                'appended_size': len(content)
            }

            self._log_operation('append', filepath, result)
            return result

        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'filepath': filepath
            }
            self._log_operation('append', filepath, result)
            return result

    def delete_file(self, filepath: str) -> Dict[str, Any]:
        """
        Delete a file

        Args:
            filepath: Path to file

        Returns:
            Dictionary with operation result
        """
        try:
            full_path = self._get_safe_path(filepath)

            if not full_path.exists():
                return {
                    'success': False,
                    'error': 'File not found',
                    'filepath': filepath
                }

            full_path.unlink()

            result = {
                'success': True,
                'filepath': str(full_path)
            }

            self._log_operation('delete', filepath, result)
            return result

        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'filepath': filepath
            }
            self._log_operation('delete', filepath, result)
            return result

    def list_files(self, directory: str = ".") -> Dict[str, Any]:
        """
        List files in a directory

        Args:
            directory: Directory path (relative to base)

        Returns:
            Dictionary with list of files
        """
        try:
            full_path = self._get_safe_path(directory)

            if not full_path.exists():
                return {
                    'success': False,
                    'error': 'Directory not found',
                    'directory': directory
                }

            files = []
            for item in full_path.iterdir():
                files.append({
                    'name': item.name,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else 0
                })

            result = {
                'success': True,
                'directory': str(full_path),
                'files': files,
                'count': len(files)
            }

            self._log_operation('list', directory, {'success': True, 'count': len(files)})
            return result

        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'directory': directory
            }
            self._log_operation('list', directory, result)
            return result

    def file_exists(self, filepath: str) -> bool:
        """Check if a file exists"""
        try:
            full_path = self._get_safe_path(filepath)
            return full_path.exists()
        except:
            return False

    def write_json(self, filepath: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write data as JSON file"""
        try:
            json_content = json.dumps(data, indent=2)
            return self.write_file(filepath, json_content)
        except Exception as e:
            return {
                'success': False,
                'error': f"JSON serialization error: {str(e)}",
                'filepath': filepath
            }

    def read_json(self, filepath: str) -> Dict[str, Any]:
        """Read JSON file"""
        result = self.read_file(filepath)

        if not result['success']:
            return result

        try:
            data = json.loads(result['content'])
            return {
                'success': True,
                'data': data,
                'filepath': filepath
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"JSON parsing error: {str(e)}",
                'filepath': filepath
            }

    def _get_safe_path(self, filepath: str) -> Path:
        """
        Get safe path within base directory

        Args:
            filepath: Requested filepath

        Returns:
            Safe resolved path

        Raises:
            ValueError: If path escapes base directory
        """
        # Resolve path
        requested_path = (self.base_directory / filepath).resolve()

        # Check if path is within base directory
        try:
            requested_path.relative_to(self.base_directory.resolve())
        except ValueError:
            raise ValueError(f"Path {filepath} is outside base directory")

        return requested_path

    def _log_operation(self, operation: str, filepath: str, result: Dict[str, Any]):
        """Log file operation"""
        self.file_history.append({
            'operation': operation,
            'filepath': filepath,
            'timestamp': datetime.now().isoformat(),
            'success': result.get('success', False)
        })

    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Get history of file operations"""
        return self.file_history.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get file operation statistics"""
        total = len(self.file_history)
        successful = sum(1 for op in self.file_history if op['success'])

        op_counts = {}
        for op in self.file_history:
            op_type = op['operation']
            op_counts[op_type] = op_counts.get(op_type, 0) + 1

        return {
            'total_operations': total,
            'successful_operations': successful,
            'failed_operations': total - successful,
            'operations_by_type': op_counts
        }