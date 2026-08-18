from datetime import datetime
import re

class TemplateEngine:
    ALLOWED_VARIABLES = {"message", "nickname", "date", "time", "anonymous_tag"}

    @classmethod
    def validate_template(cls, template_str: str) -> bool:
        variables = re.findall(r"\{(\w+)\}", template_str)
        for var in variables:
            if var not in cls.ALLOWED_VARIABLES:
                return False
        return "{message}" in template_str

    @classmethod
    def render(cls, template_str: str, message: str, nickname: str | None = None) -> str:
        now = datetime.now()
        rendered_nickname = f"#{nickname}" if nickname else ""
        anonymous_tag = "#پیام_ناشناس"
        
        payload = {
            "message": message,
            "nickname": rendered_nickname,
            "anonymous_tag": anonymous_tag,
            "date": now.strftime("%Y/%m/%d"),
            "time": now.strftime("%H:%M"),
        }
        
        out = template_str
        for k, v in payload.items():
            out = out.replace(f"{{{k}}}", v)
        return out.strip()