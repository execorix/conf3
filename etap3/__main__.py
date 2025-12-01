import argparse
import sys
import yaml

OPCODES = {
    'NEQ': 0x2, 'STORE': 0x6, 'LDI': 0x9, 'LOAD': 0xC
}
MAX_REG_ADDR = 0xF  # 4 бита (R0-R15)
MAX_MEM_ADDR_31 = 0x7FFFFFFF  # 31 бит
MAX_CONST_26 = 0x3FFFFFF  # 26 бит
INSTRUCTION_SIZE = 5


def parse_register(reg: str) -> int:
    """Извлекает индекс регистра (например, 'R7' -> 7)."""
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
        if not 0 <= value <= MAX_CONST_26: raise ValueError("Константа вне диапазона")
        base['fields'] = {'B_const': value, 'C_reg': target_reg}

    elif op == 'LOAD':
        target_reg = parse_register(instr['target_reg'])
        addr = instr['addr']
        if not 0 <= addr <= MAX_MEM_ADDR_31: raise ValueError("Адрес вне диапазона")
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    elif op == 'STORE':
        addr = instr['addr']
        source_reg = parse_register(instr['source_reg'])
        if not 0 <= addr <= MAX_MEM_ADDR_31: raise ValueError("Адрес вне диапазона")
        base['fields'] = {'B_addr': addr, 'C_reg': source_reg}

    elif op == 'NEQ':
        target_reg = parse_register(instr['target_reg'])
        addr = instr['addr']
        if not 0 <= addr <= MAX_MEM_ADDR_31: raise ValueError("Адрес вне диапазона")
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    return base


def encode_instruction(ir_instr: dict) -> bytes:
    """Трансляция из IR в 5-байтовый машинный код (Этап 2)."""
    opcode = ir_instr['opcode']
    fields = ir_instr['fields']
    instruction = 0

    if opcode == OPCODES['LDI']:
        # A (0-3), B (4-29, Константа), C (30-33, Регистр)
        B = fields['B_const'];
        C = fields['C_reg']
        instruction = opcode | (B << 4) | (C << 30)

    elif opcode == OPCODES['LOAD']:
        # A (0-3), B (4-7, Регистр), C (8-38, Адрес)
        B = fields['B_reg'];
        C = fields['C_addr']
        instruction = opcode | (B << 4) | (C << 8)

    elif opcode == OPCODES['STORE']:
        # A (0-3), B (4-34, Адрес), C (35-38, Регистр)
        B = fields['B_addr'];
        C = fields['C_reg']
        instruction = opcode | (B << 4) | (C << 35)

    elif opcode == OPCODES['NEQ']:
        # A (0-3), B (4-7, Регистр), C (8-38, Адрес)
        B = fields['B_reg'];
        C = fields['C_addr']
        instruction = opcode | (B << 4) | (C << 8)

    return instruction.to_bytes(INSTRUCTION_SIZE, byteorder='big')


def main_assembler():
    parser = argparse.ArgumentParser(description='Ассемблер для УВМ')
    parser.add_argument('input', help='Путь к исходному JSON/YAML-файлу')
    parser.add_argument('output', help='Путь к выходному бинарному файлу')
    parser.add_argument('--test', action='store_true', help='Режим тестирования')
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            program = yaml.safe_load(f)

        ir = [translate_instruction(instr) for instr in program]
        binary_data = b''

        for instr in ir:
            binary_data += encode_instruction(instr)

        if not args.test:
            with open(args.output, 'wb') as bin_file:
                bin_file.write(binary_data)

        print(f"Размер двоичного файла: {len(binary_data)} байт(а)")

    except Exception as e:
        print(f"Ошибка ассемблирования: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main_assembler()