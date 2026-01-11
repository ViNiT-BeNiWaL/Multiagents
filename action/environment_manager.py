import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class EnvironmentManager:
    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root)

    def install_dependencies(self) -> List[Dict[str, str]]:
        """
        Recursively finds config files and runs install commands.
        Returns a list of failures: [{"path": str, "error": str}]
        """
        failures = []
        
        # 1. Node.js (package.json)
        for pkg_json in self.root.rglob("package.json"):
            if "node_modules" in str(pkg_json):
                continue
                
            print(f"Installing Node deps for {pkg_json.parent}")
            success, output = self._run_command(
                ["npm", "install"], 
                cwd=pkg_json.parent
            )
            
            if not success:
                failures.append({
                    "file": str(pkg_json),
                    "error": output
                })

        # 2. Python (requirements.txt)
        for req_txt in self.root.rglob("requirements.txt"):
            if "venv" in str(req_txt) or ".env" in str(req_txt):
                continue

            print(f"Installing Python deps for {req_txt.parent}")
            # Assuming 'pip' is available; might need 'pip3' depending on env
            success, output = self._run_command(
                ["pip", "install", "-r", "requirements.txt"],
                cwd=req_txt.parent
            )

            if not success:
                failures.append({
                    "file": str(req_txt),
                    "error": output
                })

        return failures

    def _run_command(self, cmd: List[str], cwd: Path) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                check=False  # We want to handle errors manually
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr + "\n" + result.stdout

        except Exception as e:
            return False, str(e)
