import xml.etree.ElementTree as ET
from typing import Dict, Any
from enum import Enum


class TestRepoMode(Enum):
    LOCAL = "local"
    REMOTE = "remote"


class ConfigError(Exception):
    """Базовое исключение для ошибок конфигурации"""
    pass


class ConfigFileError(ConfigError):
    """Ошибка чтения/парсинга файла конфигурации"""
    pass


class ConfigValidationError(ConfigError):
    """Ошибка валидации параметров конфигурации"""
    pass


class Config:
    """Класс для работы с конфигурацией приложения"""

    def __init__(self, config_path: str = "config.xml"):
        self.config_path = config_path
        self._config_data: Dict[str, Any] = {}

    def load(self) -> None:
        """Загрузка и валидация конфигурации"""
        try:
            tree = ET.parse(self.config_path)
            root = tree.getroot()
        except FileNotFoundError:
            raise ConfigFileError(f"Конфигурационный файл не найден: {self.config_path}")
        except ET.ParseError as e:
            raise ConfigFileError(f"Ошибка парсинга XML: {e}")

        # Извлечение параметров
        self._config_data = {
            'package_name': self._get_element_text(root, 'package_name'),
            'repository_url': self._get_element_text(root, 'repository_url'),
            'test_repo_mode': self._get_element_text(root, 'test_repo_mode'),
            'package_version': self._get_element_text(root, 'package_version'),
            'filter_substring': self._get_element_text(root, 'filter_substring'),
        }

        # Валидация параметров
        self._validate_config()

    def _get_element_text(self, root: ET.Element, tag: str) -> str:
        """Извлечение текста элемента с обработкой ошибок"""
        element = root.find(tag)
        if element is None:
            raise ConfigValidationError(f"Отсутствует обязательный параметр: {tag}")
        if element.text is None:
            return ""
        return element.text.strip()

    def _validate_config(self) -> None:
        """Валидация всех параметров конфигурации"""
        # Проверка имени пакета
        package_name = self._config_data['package_name']
        if not package_name:
            raise ConfigValidationError("Имя пакета не может быть пустым")
        if len(package_name) > 100:
            raise ConfigValidationError("Имя пакета слишком длинное")

        # Проверка URL репозитория
        repo_url = self._config_data['repository_url']
        if not repo_url:
            raise ConfigValidationError("URL репозитория не может быть пустым")

        # Проверка режима работы с репозиторием
        test_repo_mode = self._config_data['test_repo_mode']
        try:
            TestRepoMode(test_repo_mode.lower())
        except ValueError:
            raise ConfigValidationError(
                f"Недопустимый режим работы с репозиторием: {test_repo_mode}. "
                f"Допустимые значения: {[mode.value for mode in TestRepoMode]}"
            )

        # Проверка версии пакета
        package_version = self._config_data['package_version']
        if not package_version:
            raise ConfigValidationError("Версия пакета не может быть пустой")

        # Подстрока фильтрации может быть пустой
        filter_substring = self._config_data['filter_substring']
        if filter_substring is None:
            self._config_data['filter_substring'] = ""

    def get_all_params(self) -> Dict[str, Any]:
        """Получение всех параметров конфигурации"""
        return self._config_data.copy()

    def get_package_name(self) -> str:
        return self._config_data['package_name']

    def get_repository_url(self) -> str:
        return self._config_data['repository_url']

    def get_test_repo_mode(self) -> str:
        return self._config_data['test_repo_mode']

    def get_package_version(self) -> str:
        return self._config_data['package_version']

    def get_filter_substring(self) -> str:
        return self._config_data['filter_substring']