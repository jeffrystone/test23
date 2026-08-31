import json


class BaseSettingsFromJson:
    path_json_config: str = " "

    def __init__(self) -> None:
        self.raw_config = config = self.upload_settings()
        for key, value in config.items():
            setattr(self, key, value)

    def upload_settings(
        self,
    ) -> dict:
        """
        :path_to_json_config - ссылка на файл .json
        """
        with open(self.path_json_config, "rb") as file:
            data = json.load(file)

        if not data or data == {}:
            raise ValueError("Конфиги отсутствуют")
        return data


class SettingsSingleton(BaseSettingsFromJson):
    _instance = None

    def __init__(self):
        if not getattr(self, "_initialized", False):
            self._initialized = True
            self._model = None

    def __new__(cls):
        if not isinstance(cls._instance, cls):
            cls._instance = super(SettingsSingleton, cls).__new__(cls)
        return cls._instance
