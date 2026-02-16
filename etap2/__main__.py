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
MAX_REG_ADDR = 0xF  # 4 бита
MAX_CONST_26 = 0x3FFFFFF  # 26 бит
MAX_ADDR_31 = 0x7FFFFFFF  # 31 бит
INSTRUCTION_SIZE = 5

def parse_register(reg_str: str) -> int:
    if not reg_str.startswith('R'):
        raise ValueError(f"Ожидался регистр в формате 'R<num>', получено: {reg_str}")
    try:
        reg_num = int(reg_str[1:])
        if not 0 <= reg_num <= MAX_REG_ADDR:
            raise ValueError(f"Номер регистра вне диапазона [R0-R{MAX_REG_ADDR}].")
        return reg_num
    except ValueError:
        raise ValueError(f"Неверный формат номера регистра: {reg_str}")


def translate_instruction(instr: dict) -> dict:
    op = instr.get('op')
    if op not in OPCODES:
        raise ValueError(f"Неизвестная операция или операция не поддерживается: {op}")

    base = {'op': op, 'opcode': OPCODES[op], 'fields': {}}

    # LDI (Константа B, Регистр C)
    if op == 'LDI':
        target_reg = parse_register(instr['target_reg'])
        value = instr['value']
        base['fields'] = {'B_const': value, 'C_reg': target_reg}

    # LOAD (Регистр B, Адрес C)
    elif op == 'LOAD':
        target_reg = parse_register(instr['target_reg'])
        addr = instr['addr']
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    # STORE (Адрес B, Регистр C)
    elif op == 'STORE':
        source_reg = parse_register(instr['source_reg'])
        addr = instr['addr']
        base['fields'] = {'B_addr': addr, 'C_reg': source_reg}

    # NEQ (Регистр B, Адрес C)
    elif op == 'NEQ':
        target_reg = parse_register(instr['target_reg'])
        addr = instr['addr']
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    return base

def check_range(value: int, max_val: int, field_name: str, op_name: str):
    if not 0 <= value <= max_val:
        raise ValueError(
            f"Переполнение в команде {op_name}: {field_name} ({value}) выходит за допустимый максимум (0x{max_val:X}).")


def assemble_instruction(ir_instr: Dict[str, Any]) -> bytes:
    opcode = ir_instr['opcode']
    fields = ir_instr['fields']
    op_name = ir_instr['op']
    instr_word = 0
    instr_word |= (opcode & 0xF)

    if op_name == 'LDI':
        b_val = fields.get('B_const', 0)
        c_val = fields.get('C_reg', 0)

        check_range(b_val, MAX_CONST_26, 'B_const', op_name)
        check_range(c_val, MAX_REG_ADDR, 'C_reg', op_name)

        instr_word |= (b_val & MAX_CONST_26) << 4
        instr_word |= (c_val & MAX_REG_ADDR) << 30

    elif op_name in ('LOAD', 'NEQ'):
        b_val = fields.get('B_reg', 0)
        c_val = fields.get('C_addr', 0)

        check_range(b_val, MAX_REG_ADDR, 'B_reg', op_name)
        check_range(c_val, MAX_ADDR_31, 'C_addr', op_name)

        instr_word |= (b_val & MAX_REG_ADDR) << 4
        instr_word |= (c_val & MAX_ADDR_31) << 8

    elif op_name == 'STORE':
        b_val = fields.get('B_addr', 0)
        c_val = fields.get('C_reg', 0)

        check_range(b_val, MAX_ADDR_31, 'B_addr', op_name)
        check_range(c_val, MAX_REG_ADDR, 'C_reg', op_name)

        instr_word |= (b_val & MAX_ADDR_31) << 4
        instr_word |= (c_val & MAX_REG_ADDR) << 35
    return instr_word.to_bytes(INSTRUCTION_SIZE, byteorder='little')


def assemble_program(ir_program: List[Dict[str, Any]], target_path: str):
    binary_program = b''.join([assemble_instruction(instr) for instr in ir_program])

    with open(target_path, 'wb') as f:
        f.write(binary_program)

def print_ir_fields(ir_program: List[Dict[str, Any]]):
    """Выводит промежуточное представление (IR) в читаемом формате."""
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
    parser = argparse.ArgumentParser(description='Ассемблер УВМ (Этап 2: Генерация бинарного кода)')
    parser.add_argument('source', help='Путь к исходному файлу программы (JSON/YAML)')
    parser.add_argument('target', help='Путь для сохранения бинарного файла')
    parser.add_argument('--test-mode', action='store_true',
                        help='Включить режим тестирования. Выводит IR и не генерирует бинарный файл.')
    args = parser.parse_args()
    try:
        with open(args.source, 'r', encoding='utf-8') as f:
            source_code = yaml.safe_load(f)
        ir_program = [translate_instruction(instr) for instr in source_code]
        if args.test_mode:
            print_ir_fields(ir_program)
            print("---")
            print("Режим тестирования завершен.")
            return
        assemble_program(ir_program, args.target)

        print(f"Ассемблирование завершено.")
        print(f"Бинарный файл сохранен в: {args.target}")
        print(f"Проверено {len(ir_program)} команд.")

    except Exception as e:
        print(f"Ошибка при ассемблировании: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main_assembler()