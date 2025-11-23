#!/usr/bin/env python3
import sys
import argparse
from config import Config, ConfigError, ConfigFileError, ConfigValidationError


def print_config_params(config_data: dict) -> None:
    """Вывод параметров конфигурации в формате ключ-значение"""
    print("=" * 50)
    print("ПАРАМЕТРЫ КОНФИГУРАЦИИ")
    print("=" * 50)

    for key, value in config_data.items():
        print(f"{key:<20}: {value}")

    print("=" * 50)


def main():
    """Основная функция приложения"""
    parser = argparse.ArgumentParser(
        description="Минимальное CLI-приложение с конфигурацией XML"
    )
    parser.add_argument(
        "--config",
        default="config.xml",
        help="Путь к конфигурационному файлу (по умолчанию: config.xml)"
    )

    args = parser.parse_args()

    try:
        # Загрузка конфигурации
        config = Config(args.config)
        config.load()

        # Получение всех параметров
        config_data = config.get_all_params()

        # Вывод параметров
        print_config_params(config_data)
        print("\nРабота с параметрами:")
        print(f"Анализируемый пакет: {config.get_package_name()}")
        print(f"Режим работы: {config.get_test_repo_mode()}")
        print(f"Фильтр: '{config.get_filter_substring()}'")

        return 0

    except ConfigFileError as e:
        print(f"Ошибка файла конфигурации: {e}", file=sys.stderr)
        return 1
    except ConfigValidationError as e:
        print(f"Ошибка валидации конфигурации: {e}", file=sys.stderr)
        return 2
    except ConfigError as e:
        print(f"Ошибка конфигурации: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Неожиданная ошибка: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())