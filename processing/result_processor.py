import re
from typing import Dict, Any, List


class ResultProcessor:
    def __init__(self, file_manager):
        self.fm = file_manager

    def create_complete_implementation(
        self, task: str, results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        created_files = []

        for _, content in results.items():
            if not isinstance(content, str):
                continue

            # NEW: Try to find explicitly labeled files first
            labeled_files = self._extract_labeled_files(content)
            if labeled_files:
                for file_info in labeled_files:
                    created_files.append(
                        self.fm.write_file(file_info["path"], file_info["content"])
                    )
                continue

            # FALLBACK: Legacy HTML/CSS/JS scraping
            blocks = re.findall(
                r"```(\w+)\n(.*?)```",
                content,
                re.DOTALL
            )

            for lang, code in blocks:
                lang = lang.lower()

                if lang == "html":
                    created_files.extend(
                        self._process_html(code)
                    )

                elif lang == "css":
                    created_files.append(
                        self.fm.write_file("style.css", code.strip())
                    )

                elif lang in ("js", "javascript"):
                    created_files.append(
                        self.fm.write_file("script.js", code.strip())
                    )

        return created_files

    def _extract_labeled_files(self, content: str) -> List[Dict[str, str]]:
        """
        Parses content looking for:
        ### FILE: path/to/file.ext
        ```lang
        code...
        ```
        """
        files = []
        # Regex finds "### FILE: <path>" followed somewhat closely by a code block
        pattern = r"### FILE: ([\w/.-]+)\s+```\w*\n(.*?)```"
        
        matches = re.findall(pattern, content, re.DOTALL)
        
        for path, code in matches:
            files.append({
                "path": path.strip(),
                "content": code.strip()
            })
            
        return files

    # -----------------------------
    # HTML SPLITTING LOGIC
    # -----------------------------

    def _process_html(self, html: str) -> List[Dict[str, Any]]:
        created = []

        # Extract <style>...</style>
        css_blocks = re.findall(
            r"<style.*?>(.*?)</style>",
            html,
            re.DOTALL
        )

        # Extract <script>...</script>
        js_blocks = re.findall(
            r"<script.*?>(.*?)</script>",
            html,
            re.DOTALL
        )

        css_content = "\n\n".join(
            block.strip() for block in css_blocks
        )
        js_content = "\n\n".join(
            block.strip() for block in js_blocks
        )

        # Remove inline CSS & JS from HTML
        html = re.sub(
            r"<style.*?>.*?</style>",
            "",
            html,
            flags=re.DOTALL
        )
        html = re.sub(
            r"<script.*?>.*?</script>",
            "",
            html,
            flags=re.DOTALL
        )

        # Inject external references
        html = self._inject_links(html)

        # Write files
        created.append(
            self.fm.write_file("index.html", html.strip())
        )

        if css_content:
            created.append(
                self.fm.write_file("style.css", css_content)
            )

        if js_content:
            created.append(
                self.fm.write_file("script.js", js_content)
            )

        return created

    # -----------------------------
    # HTML REWRITE
    # -----------------------------

    def _inject_links(self, html: str) -> str:
        # Add CSS link before </head>
        if "</head>" in html:
            html = html.replace(
                "</head>",
                '    <link rel="stylesheet" href="style.css">\n</head>'
            )

        # Add JS before </body>
        if "</body>" in html:
            html = html.replace(
                "</body>",
                '    <script src="script.js"></script>\n</body>'
            )

        return html
