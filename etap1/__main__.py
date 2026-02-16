import argparse
import sys
import yaml
from typing import Dict, Any, List, Optional

# Константы УВМ
OPCODES = {
    'NEQ': 0x2,
    'STORE': 0x6,
    'LDI': 0x9,
    'LOAD': 0xC
}
MAX_REG_ADDR = 0xF


def parse_register(reg_str: str) -> Optional[int]:
    if not reg_str.startswith('R'):
        print(f"ОШИБКА: Ожидался регистр в формате 'R<num>', получено: {reg_str}", file=sys.stderr)
        return None
    try:
        reg_num = int(reg_str[1:])
        if not 0 <= reg_num <= MAX_REG_ADDR:
            print(f"ОШИБКА: Номер регистра вне диапазона [R0-R{MAX_REG_ADDR}]: {reg_str}", file=sys.stderr)
            return None
        return reg_num
    except ValueError:
        print(f"ОШИБКА: Неверный формат номера регистра: {reg_str}", file=sys.stderr)
        return None


def translate_instruction(instr: dict) -> Optional[dict]:
    op = instr.get('op')
    if op not in OPCODES:
        print(f"ОШИБКА: Неизвестная операция или операция не поддерживается минимальным ассемблером: {op}", file=sys.stderr)
        return None

    base = {'op': op, 'opcode': OPCODES[op], 'fields': {}}

    if op == 'LDI':
        target_reg = parse_register(instr.get('target_reg', ''))
        value = instr.get('value')

        if target_reg is None: return None
        base['fields'] = {'B_const': value, 'C_reg': target_reg}

    elif op == 'LOAD':
        target_reg = parse_register(instr.get('target_reg', ''))
        addr = instr.get('addr')

        if target_reg is None: return None
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    elif op == 'STORE':
        source_reg = parse_register(instr.get('source_reg', ''))
        addr = instr.get('addr')

        if source_reg is None: return None
        base['fields'] = {'B_addr': addr, 'C_reg': source_reg}

    elif op == 'NEQ':
        target_reg = parse_register(instr.get('target_reg', ''))
        addr = instr.get('addr')

        if target_reg is None: return None
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    return base

# --- Функции вывода ---

def print_ir_fields(ir_program: List[Dict[str, Any]]):
    print("=========================================================================")
    print("Промежуточное Представление (IR) в режиме тестирования:")
    print("-------------------------------------------------------------------------")
    for i, ir_instr in enumerate(ir_program):
        op_name = ir_instr['op']
        opcode = ir_instr['opcode']
        fields = ir_instr['fields']

        field_str = ', '.join([f"{k}: {v}" for k, v in fields.items()])

        print(f"[{i:03d}] {op_name} (0x{opcode:0X}): {field_str}")

    print("=========================================================================")


def main_assembler():
    """Главная функция ассемблера."""
    parser = argparse.ArgumentParser(description='Ассемблер УВМ (Этап 1: IR)')
    parser.add_argument('source', help='Путь к исходному файлу программы (JSON/YAML)')
    parser.add_argument('target', help='Путь для сохранения бинарного файла')
    parser.add_argument('--test-mode', action='store_true',
                        help='Включить режим тестирования. Выводит IR и не генерирует бинарный файл.')

    args = parser.parse_args()

    try:
        with open(args.source, 'r', encoding='utf-8') as f:
            source_code = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ОШИБКА: Файл не найден: {args.source}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ОШИБКА: Не удалось прочитать или разобрать исходный файл: {e}", file=sys.stderr)
        sys.exit(1)

    ir_program = []
    for instr in source_code:
        translated = translate_instruction(instr)
        if translated is not None:
            ir_program.append(translated)
        else:
            print(f"ПРЕДУПРЕЖДЕНИЕ: Инструкция {instr} пропущена из-за ошибки трансляции.", file=sys.stderr)


    if not ir_program and source_code:
        print("ОШИБКА: Ни одна инструкция не была успешно транслирована.", file=sys.stderr)
        sys.exit(1)

    if args.test_mode:
        print_ir_fields(ir_program)
        print("---")
        print("Режим тестирования завершен.")
        return

    print(f"Трансляция в IR завершена (количество команд: {len(ir_program)}).")
    print(f"Для вывода IR используйте: python {sys.argv[0]} {args.source} {args.target} --test-mode")

if __name__ == '__main__':
    main_assembler()