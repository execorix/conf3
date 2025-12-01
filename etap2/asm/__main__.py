import argparse
import json
import sys
import yaml

OPCODES = {
    'NEQ': 0x2,  # != (A=2)
    'STORE': 0x6,  # Запись в память (A=6)
    'LDI': 0x9,  # Загрузка константы (A=9)
    'LOAD': 0xC  # Чтение из памяти (A=12)
}
MAX_REG_ADDR = 0xF  # 4 бита (0-15)
MAX_MEM_ADDR_31 = 0x7FFFFFFF  # 31 бит
MAX_CONST_26 = 0x3FFFFFF  # 26 бит
INSTRUCTION_SIZE = 5  # Размер команды в байтах


def parse_register(reg: str) -> int:
    if not reg.startswith('R') or not reg[1:].isdigit():
        raise ValueError(f"Некорректный регистр: {reg}")
    reg_idx = int(reg[1:])
    if not 0 <= reg_idx <= MAX_REG_ADDR:
        raise ValueError(f"Регистр вне диапазона [R0-R{MAX_REG_ADDR}]: {reg}")
    return reg_idx


def translate_instruction(instr: dict) -> dict:
    """Транслирует JSON-команду во внутреннее представление (IR)."""
    op = instr['op']
    if op not in OPCODES:
        raise ValueError(f"Неизвестная операция: {op}")

    base = {'op': op, 'opcode': OPCODES[op], 'fields': {}}

    if op == 'LDI':
        value = instr['value']
        target_reg = parse_register(instr['target_reg'])
        if not 0 <= value <= MAX_CONST_26:
            raise ValueError(f"Константа {value} вне диапазона (0-{MAX_CONST_26})")
        base['fields'] = {'B_const': value, 'C_reg': target_reg}

    elif op == 'LOAD':
        target_reg = parse_register(instr['target_reg'])
        addr = instr['addr']
        if not 0 <= addr <= MAX_MEM_ADDR_31:
            raise ValueError(f"Адрес {addr} вне диапазона (0-{MAX_MEM_ADDR_31})")
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    elif op == 'STORE':
        addr = instr['addr']
        source_reg = parse_register(instr['source_reg'])
        if not 0 <= addr <= MAX_MEM_ADDR_31:
            raise ValueError(f"Адрес {addr} вне диапазона (0-{MAX_MEM_ADDR_31})")
        # Поле B: Адрес (31b), Поле C: Регистр (4b)
        base['fields'] = {'B_addr': addr, 'C_reg': source_reg}

    elif op == 'NEQ':
        target_reg = parse_register(instr['target_reg'])
        addr = instr['addr']
        if not 0 <= addr <= MAX_MEM_ADDR_31:
            raise ValueError(f"Адрес {addr} вне диапазона (0-{MAX_MEM_ADDR_31})")
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    return base

def encode_instruction(ir_instr: dict) -> bytes:
    opcode = ir_instr['opcode']
    fields = ir_instr['fields']
    instruction = 0


    if opcode == OPCODES['LDI']:
        B = fields['B_const']
        C = fields['C_reg']
        instruction = opcode  # A (0-3)
        instruction |= (B << 4)  # B (4-29)
        instruction |= (C << 30)  # C (30-33)

    elif opcode == OPCODES['LOAD']:
        B = fields['B_reg']
        C = fields['C_addr']
        instruction = opcode  # A (0-3)
        instruction |= (B << 4)  # B (4-7)
        instruction |= (C << 8)  # C (8-38)

    elif opcode == OPCODES['STORE']:
        B = fields['B_addr']
        C = fields['C_reg']
        instruction = opcode  # A (0-3)
        instruction |= (B << 4)  # B (4-34)
        instruction |= (C << 35)  # C (35-38)
    elif opcode == OPCODES['NEQ']:
        B = fields['B_reg']
        C = fields['C_addr']
        instruction = opcode  # A (0-3)
        instruction |= (B << 4)  # B (4-7)
        instruction |= (C << 8)  # C (8-38)
    return instruction.to_bytes(INSTRUCTION_SIZE, byteorder='big')


def format_bytes_for_test(binary_data: bytes) -> str:
    return ', '.join(f'0x{b:02X}' for b in binary_data)

def main_assembler():
    parser = argparse.ArgumentParser(description='Ассемблер для УВМ (Этап 2)')
    parser.add_argument('input', help='Путь к исходному JSON/YAML-файлу')
    parser.add_argument('output', help='Путь к выходному бинарному файлу')
    parser.add_argument('--test', action='store_true',
                        help='Режим тестирования: вывод внутреннего представления и байтов')
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            program = yaml.safe_load(f)

        ir = [translate_instruction(instr) for instr in program]
        binary_data = b''

        if args.test:
            print("--- Тестирование Этапа 2 (Машинный код) ---")

        for i, instr in enumerate(ir):
            instr_bytes = encode_instruction(instr)
            binary_data += instr_bytes
            if args.test:
                print(f"Инструкция {i} ({instr['op']}):")
                print(f"  Ожидаемые поля: {instr['fields']}")
                print(f"  Машинный код (5 байт): {format_bytes_for_test(instr_bytes)}")

        with open(args.output, 'wb') as bin_file:
            bin_file.write(binary_data)
        file_size = len(binary_data)
        print(f"\nРазмер двоичного файла: {file_size} байт(а)")

    except Exception as e:
        print(f"Ошибка ассемблирования: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main_assembler()