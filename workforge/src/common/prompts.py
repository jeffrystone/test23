import logging
import re
import string

from .json_configs import BaseSettingsFromJson

logger = logging.getLogger(__name__)


class Prompts(BaseSettingsFromJson):
    path_json_config = "./prompts/prompts.json"
    _prompt_var_regex = re.compile(r"\$(\w+)")

    def __init__(self):
        self.prompts_mapping = {}
        config = self.upload_settings()

        for key, value in config.items():
            self.prompts_mapping[key] = value

            if isinstance(value, str):
                try:
                    content = self.load(value)
                    setattr(self, key, content)
                except FileNotFoundError:
                    logger.error(f"Prompt file not found: {value}")
                    setattr(self, key, value)
                except Exception as e:
                    logger.error(f"Error reading prompt file {value}: {str(e)}")
                    setattr(self, key, value)
            else:
                setattr(self, key, value)

    def get_prompt(self, key: str, force: bool = False):
        if not force:
            return getattr(self, key)

        filepath = self.prompts_mapping[key]
        return self.load(filepath)

    @classmethod
    def load(cls, filepath) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content

    def recursive_substitution_prompts(self, head_prompt) -> str:
        """return final prompt which consists of other prompts"""
        all_variables = self._prompt_var_regex.findall(head_prompt)
        nested_prompts = [
            prompt_name for prompt_name in all_variables if hasattr(self, prompt_name)
        ]

        if not nested_prompts:
            return head_prompt

        other_prompts = {np: self.get_prompt(np) for np in nested_prompts}
        new_template = string.Template(head_prompt)
        new_template = new_template.safe_substitute(**other_prompts)
        return self.recursive_substitution_prompts(new_template)

    @classmethod
    def get_final_prompt(cls, key) -> str:
        """return: final prompt template and head prompt name"""
        all_prompts = cls()
        head_prompt = all_prompts.get_prompt(key)
        return all_prompts.recursive_substitution_prompts(head_prompt)
