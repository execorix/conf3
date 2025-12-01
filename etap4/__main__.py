import argparse
import sys
import yaml

# --- СПЕЦИФИКАЦИЯ УВМ (Обновлено для Этапа 4) ---
OPCODES = {
    'NEQ': 0x2,
    'ADD': 0x3,  #  Сложение Reg-Reg
    'SUB': 0x4,  #  Вычитание Reg-Reg
    'JMP': 0x5,  #  Безусловный переход
    'JZ': 0x6,  # Условный переход
    'STORE': 0x6,
    'LDI': 0x9,
    'LOAD': 0xC
}
# ... (Остальные константы без изменений) ...
MAX_REG_ADDR = 0xF
MAX_MEM_ADDR_31 = 0x7FFFFFFF
INSTRUCTION_SIZE = 5


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

    # ... (LOAD, LDI, STORE, NEQ логика остается без изменений) ...
    # НОВЫЕ ОПЕРАЦИИ (Регистр-Регистр)
    if op in ('ADD', 'SUB'):
        # Синтаксис: R[A] = R[B] + R[C] (Используем B для target, C для source)
        reg_b = parse_register(instr['target_reg'])
        reg_c = parse_register(instr['source_reg'])
        # A(4b) | B_reg(4b) | C_reg(4b) | 28 неисп.
        base['fields'] = {'B_reg': reg_b, 'C_reg': reg_c}

    elif op == 'JMP':
        addr = instr['addr']
        if not 0 <= addr <= MAX_MEM_ADDR_31: raise ValueError("Адрес перехода вне диапазона")
        base['fields'] = {'B_addr': addr}

    elif op == 'JZ':
        reg_b = parse_register(instr['condition_reg'])
        addr_c = instr['addr']
        if not 0 <= addr_c <= MAX_MEM_ADDR_31: raise ValueError("Адрес перехода вне диапазона")
        base['fields'] = {'B_reg': reg_b, 'C_addr': addr_c}

    elif op == 'LDI':
        value = instr['value'];
        target_reg = parse_register(instr['target_reg'])
        base['fields'] = {'B_const': value, 'C_reg': target_reg}
    elif op == 'LOAD':
        target_reg = parse_register(instr['target_reg']);
        addr = instr['addr']
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}
    elif op == 'STORE':
        addr = instr['addr'];
        source_reg = parse_register(instr['source_reg'])
        base['fields'] = {'B_addr': addr, 'C_reg': source_reg}
    elif op == 'NEQ':
        target_reg = parse_register(instr['target_reg']);
        addr = instr['addr']
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    return base


def encode_instruction(ir_instr: dict) -> bytes:
    opcode = ir_instr['opcode']
    fields = ir_instr['fields']
    instruction = 0

    if opcode in (OPCODES['ADD'], OPCODES['SUB']):
        # A (0-3), B (4-7, Регистр), C (8-11, Регистр)
        B = fields['B_reg'];
        C = fields['C_reg']
        instruction = opcode | (B << 4) | (C << 8)

    # НОВЫЕ ОПЕРАЦИИ (JMP/JZ)
    elif opcode == OPCODES['JMP']:
        # A (0-3), B (4-39, Адрес, используем 36 бит)
        B = fields['B_addr']
        # Используем 36 бит для адреса (40 - 4 = 36), чтобы заполнить оставшуюся команду.
        instruction = opcode | (B << 4)

    elif opcode == OPCODES['JZ']:
        # A (0-3), B (4-7, Регистр), C (8-38, Адрес)
        B = fields['B_reg'];
        C = fields['C_addr']
        instruction = opcode | (B << 4) | (C << 8)

    # ... (LOAD, LDI, STORE, NEQ логика ниже для полноты) ...
    elif opcode == OPCODES['LDI']:
        B = fields['B_const'];
        C = fields['C_reg']
        instruction = opcode | (B << 4) | (C << 30)
    elif opcode == OPCODES['LOAD'] or opcode == OPCODES['NEQ']:
        B = fields['B_reg'];
        C = fields['C_addr']
        instruction = opcode | (B << 4) | (C << 8)
    elif opcode == OPCODES['STORE']:
        B = fields['B_addr'];
        C = fields['C_reg']
        instruction = opcode | (B << 4) | (C << 35)

    return instruction.to_bytes(INSTRUCTION_SIZE, byteorder='big')

def main_assembler():
    parser = argparse.ArgumentParser(description='Ассемблер для УВМ (Этап 4)')
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