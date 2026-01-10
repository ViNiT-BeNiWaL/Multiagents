class SecurityLevel:
    MEDIUM = "medium"

class SecurityValidator:
    def validate_command(self, text: str, level):
        forbidden = ["rm -rf", "eval(", "exec("]
        for f in forbidden:
            if f in text.lower():
                return False, "Forbidden command"
        return True, "OK"
