"""
Result processor for converting task results into actual files

Add this import to your orchestrator.py:
from result_processor import ResultProcessor

Then in MultiAgentOrchestrator.__init__():
    self.result_processor = ResultProcessor(self.file_manager)

And in execute_task(), after getting results, add:
    # Generate actual files from results
    created_files = self.result_processor.create_complete_implementation(
        task_description, 
        results
    )
    
    # Display created files
    if created_files:
        self.console.print("\n[bold green]Created Files:[/bold green]")
        for file_info in created_files:
            self.console.print(f"  ✓ {file_info['filename']} ({file_info['type']}, {file_info['size']} bytes)")
"""
import json
import re
from typing import Dict, Any, List
from pathlib import Path
from action.file_manager import FileManager


class ResultProcessor:
    """Processes task results and generates appropriate output files"""

    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager

    def process_result(self, task_description: str, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process results and generate appropriate files based on task type
        
        Args:
            task_description: Original task description
            results: Dictionary of subtask results
            
        Returns:
            List of created files with their information
        """
        created_files = []
        
        # Detect task type and process accordingly
        if self._is_coding_task(task_description):
            created_files.extend(self._process_code_results(results))
        
        if self._is_documentation_task(task_description):
            created_files.extend(self._process_documentation_results(results))
            
        if self._is_analysis_task(task_description):
            created_files.extend(self._process_analysis_results(results))
        
        return created_files

    def _is_coding_task(self, task: str) -> bool:
        """Check if task involves code generation"""
        code_keywords = ['function', 'code', 'program', 'implement', 'algorithm', 'python', 'class']
        return any(keyword in task.lower() for keyword in code_keywords)

    def _is_documentation_task(self, task: str) -> bool:
        """Check if task involves documentation"""
        doc_keywords = ['document', 'readme', 'guide', 'specification', 'documentation']
        return any(keyword in task.lower() for keyword in doc_keywords)

    def _is_analysis_task(self, task: str) -> bool:
        """Check if task involves analysis"""
        analysis_keywords = ['analyze', 'analysis', 'compare', 'evaluate', 'review']
        return any(keyword in task.lower() for keyword in analysis_keywords)

    def _process_code_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and save code from results"""
        created_files = []
        
        for subtask_id, result in results.items():
            if not isinstance(result, str):
                continue
                
            # Extract all code blocks from the result
            code_blocks = self._extract_code_blocks(result)
            
            for i, code_block in enumerate(code_blocks):
                # Determine file extension and name
                language = code_block.get('language', 'python')
                extension = self._get_file_extension(language)
                
                # Generate filename
                if 'test' in result.lower():
                    filename = f"test_sorting_{i+1}.{extension}"
                elif 'example' in result.lower():
                    filename = f"example_usage_{i+1}.{extension}"
                else:
                    filename = f"sorting_function_{i+1}.{extension}"
                
                # Write the code file
                file_result = self.file_manager.write_file(
                    filename,
                    code_block['code']
                )
                
                if file_result['success']:
                    created_files.append({
                        'filename': filename,
                        'type': 'code',
                        'language': language,
                        'size': file_result['size']
                    })
        
        return created_files

    def _process_documentation_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and save documentation from results"""
        created_files = []
        
        # Combine all documentation
        documentation = []
        
        for subtask_id, result in results.items():
            if isinstance(result, str):
                # Remove code blocks for documentation
                doc_text = self._remove_code_blocks(result)
                if doc_text.strip():
                    documentation.append(f"## {subtask_id}\n\n{doc_text}\n")
        
        if documentation:
            # Create README
            readme_content = "# Sorting Function Documentation\n\n"
            readme_content += "\n".join(documentation)
            
            file_result = self.file_manager.write_file(
                "SORTING_README.md",
                readme_content
            )
            
            if file_result['success']:
                created_files.append({
                    'filename': 'SORTING_README.md',
                    'type': 'documentation',
                    'size': file_result['size']
                })
        
        return created_files

    def _process_analysis_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Save analysis results as markdown report"""
        created_files = []
        
        # Create analysis report
        report_content = "# Analysis Report\n\n"
        
        for subtask_id, result in results.items():
            if isinstance(result, str):
                report_content += f"## {subtask_id}\n\n{result}\n\n"
        
        file_result = self.file_manager.write_file(
            "analysis_report.md",
            report_content
        )
        
        if file_result['success']:
            created_files.append({
                'filename': 'analysis_report.md',
                'type': 'analysis',
                'size': file_result['size']
            })
        
        return created_files

    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extract code blocks from markdown-style text"""
        code_blocks = []
        
        # Pattern for fenced code blocks with language
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            language = match.group(1) or 'python'
            code = match.group(2).strip()
            
            if code:
                code_blocks.append({
                    'language': language,
                    'code': code
                })
        
        # If no fenced blocks, look for indented code
        if not code_blocks:
            lines = text.split('\n')
            current_code = []
            in_code_block = False
            
            for line in lines:
                if line.startswith('    ') or line.startswith('\t'):
                    in_code_block = True
                    current_code.append(line.lstrip())
                elif in_code_block and line.strip():
                    # End of code block
                    if current_code:
                        code_blocks.append({
                            'language': 'python',
                            'code': '\n'.join(current_code)
                        })
                        current_code = []
                    in_code_block = False
            
            # Add last block if exists
            if current_code:
                code_blocks.append({
                    'language': 'python',
                    'code': '\n'.join(current_code)
                })
        
        return code_blocks

    def _remove_code_blocks(self, text: str) -> str:
        """Remove code blocks from text"""
        # Remove fenced code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Remove indented code blocks (4 spaces or tab)
        lines = text.split('\n')
        non_code_lines = [line for line in lines if not (line.startswith('    ') or line.startswith('\t'))]
        
        return '\n'.join(non_code_lines)

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rust': 'rs',
            'typescript': 'ts'
        }
        return extensions.get(language.lower(), 'txt')

    def create_complete_implementation(self, task_description: str, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create a complete implementation with all necessary files
        
        Args:
            task_description: Original task description
            results: All subtask results
            
        Returns:
            List of all created files
        """
        created_files = []
        
        # 1. Extract and save all code implementations
        code_files = self._process_code_results(results)
        created_files.extend(code_files)
        
        # 2. Create main implementation file if multiple code files exist
        if len(code_files) > 1:
            main_file = self._create_main_implementation(results)
            if main_file:
                created_files.append(main_file)
        
        # 3. Create documentation
        doc_files = self._process_documentation_results(results)
        created_files.extend(doc_files)
        
        # 4. Create requirements file if needed
        requirements_file = self._create_requirements_file(results)
        if requirements_file:
            created_files.append(requirements_file)
        
        return created_files

    def _create_main_implementation(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create main implementation file combining all code"""
        all_code = []
        
        for subtask_id, result in results.items():
            if isinstance(result, str):
                code_blocks = self._extract_code_blocks(result)
                for block in code_blocks:
                    if 'test' not in result.lower():  # Skip test code in main
                        all_code.append(f"# {subtask_id}\n{block['code']}\n")
        
        if all_code:
            main_content = '"""Main sorting implementation"""\n\n'
            main_content += '\n\n'.join(all_code)
            
            file_result = self.file_manager.write_file(
                "sorting_implementation.py",
                main_content
            )
            
            if file_result['success']:
                return {
                    'filename': 'sorting_implementation.py',
                    'type': 'main_implementation',
                    'size': file_result['size']
                }
        
        return None

    def _create_requirements_file(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create requirements.txt if dependencies are mentioned"""
        dependencies = set()
        
        # Common dependency keywords
        dep_keywords = {
            'numpy': 'numpy',
            'pandas': 'pandas',
            'matplotlib': 'matplotlib',
            'scipy': 'scipy',
            'requests': 'requests'
        }
        
        for result in results.values():
            if isinstance(result, str):
                result_lower = result.lower()
                for keyword, package in dep_keywords.items():
                    if keyword in result_lower:
                        dependencies.add(package)
        
        if dependencies:
            requirements_content = '\n'.join(sorted(dependencies))
            
            file_result = self.file_manager.write_file(
                "requirements.txt",
                requirements_content
            )
            
            if file_result['success']:
                return {
                    'filename': 'requirements.txt',
                    'type': 'dependencies',
                    'size': file_result['size']
                }
        
        return None