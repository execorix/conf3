import argparse
import sys
import yaml

OPCODES = {
    'NOP': 0x0,
    'NEQ': 0x2, 'ADD': 0x3, 'SUB': 0x4,
    'JMP': 0x5, 'JZ': 0x6,
    'IN': 0x7, 'OUT': 0x8,
    'LDI': 0x9, 'STORE': 0xA, 'LOAD': 0xC
}
MAX_CONST_26 = 0x3FFFFFF
INSTRUCTION_SIZE = 5
def parse_register(reg_str: str) -> int:
    if not reg_str.startswith('R'):
        raise ValueError(f"Ожидался регистр в формате 'R<num>', получено: {reg_str}")
    try:
        reg_num = int(reg_str[1:])
        if not 0 <= reg_num < 16:
            raise ValueError("Номер регистра должен быть в диапазоне 0-15.")
        return reg_num
    except ValueError:
        raise ValueError(f"Неверный формат номера регистра: {reg_str}")


def translate_instruction(instr: dict) -> dict:
    op = instr['op']
    if op not in OPCODES: raise ValueError(f"Неизвестная операция: {op}")

    base = {'op': op, 'opcode': OPCODES[op], 'fields': {}}

    if op == 'NOP':
        base['fields'] = {}

    elif op in ('IN', 'OUT'):
        target_reg = parse_register(instr['target_reg'])
        value_code = instr['value_code']
        if not 0 <= value_code <= MAX_CONST_26: raise ValueError("Код I/O вне диапазона")
        base['fields'] = {'B_const': value_code, 'C_reg': target_reg}

    elif op in ('ADD', 'SUB'):
        reg_b = parse_register(instr['target_reg'])
        reg_c = parse_register(instr['source_reg'])
        base['fields'] = {'B_reg': reg_b, 'C_reg': reg_c}

    elif op == 'JMP':
        addr = instr['addr']
        base['fields'] = {'B_addr': addr}

    elif op == 'JZ':
        reg_b = parse_register(instr['condition_reg'])
        addr_c = instr['addr']
        base['fields'] = {'B_reg': reg_b, 'C_addr': addr_c}

    elif op == 'LDI':
        value = instr['value']
        target_reg = parse_register(instr['target_reg'])
        base['fields'] = {'B_const': value, 'C_reg': target_reg}

    elif op == 'LOAD':
        target_reg = parse_register(instr['target_reg'])
        addr = instr['addr']
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    elif op == 'STORE':
        addr = instr['addr']
        source_reg = parse_register(instr['source_reg'])
        base['fields'] = {'B_addr': addr, 'C_reg': source_reg}

    elif op == 'NEQ':
        target_reg = parse_register(instr['target_reg'])
        addr = instr['addr']
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    return base


def encode_instruction(ir_instr: dict) -> bytes:
    opcode = ir_instr['opcode']
    fields = ir_instr['fields']
    instruction = 0

    if opcode == OPCODES['NOP']:
        instruction = 0

    elif opcode in (OPCODES['IN'], OPCODES['OUT'], OPCODES['LDI']):
        B = fields['B_const']
        C = fields['C_reg']
        instruction = opcode | (B << 4) | (C << 30)

    elif opcode in (OPCODES['ADD'], OPCODES['SUB']):
        B = fields['B_reg']
        C = fields['C_reg']
        instruction = opcode | (B << 4) | (C << 8)

    elif opcode == OPCODES['JMP']:
        B = fields['B_addr']
        instruction = opcode | (B << 4)

    elif opcode in (OPCODES['JZ'], OPCODES['LOAD'], OPCODES['NEQ']):
        B = fields['B_reg']
        C = fields['C_addr']
        instruction = opcode | (B << 4) | (C << 8)

    elif opcode == OPCODES['STORE']:
        B = fields['B_addr']
        C = fields['C_reg']
        instruction = opcode | (B << 4) | (C << 35)

    return instruction.to_bytes(INSTRUCTION_SIZE, byteorder='big')


def main_assembler():
    parser = argparse.ArgumentParser(description='Ассемблер УВМ (Финальный)')
    parser.add_argument('source', help='Путь к исходному файлу программы (JSON)')
    parser.add_argument('target', help='Путь для сохранения бинарного файла')
    args = parser.parse_args()

    try:
        with open(args.source, 'r', encoding='utf-8') as f:
            source_code = yaml.safe_load(f)

        ir_program = [translate_instruction(instr) for instr in source_code]

        binary_program = b''
        for ir_instr in ir_program:
            binary_program += encode_instruction(ir_instr)

        with open(args.target, 'wb') as f:
            f.write(binary_program)

        print(f"Сборка завершена. Программа из {len(ir_program)} инструкций сохранена в {args.target}")

    except Exception as e:
        print(f"Ошибка при ассемблировании: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main_assembler()