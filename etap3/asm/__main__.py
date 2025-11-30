import argparse
import json
import sys
import yaml

OPCODES = {
    'LOAD': 0x01,
    'STORE': 0x02,
    'ADD': 0x03,
    'SUB': 0x04,
    'JMP': 0x05,
    'JZ': 0x06,
    'HALT': 0x07
}
def parse_register(reg: str) -> int:
    if not reg.startswith('R') or not reg[1:].isdigit():
        raise ValueError(f"Некорректный регистр: {reg}")
    reg_idx = int(reg[1:])
    if not 0 <= reg_idx <= 3:
        raise ValueError(f"Регистр вне диапазона [R0-R3]: {reg}")
    return reg_idx
def translate_instruction(instr: dict) -> dict:
    op = instr['op']
    args = instr.get('args', [])
    if op not in OPCODES:
        raise ValueError(f"Неизвестная операция: {op}")
    base = {'opcode': OPCODES[op]}
    if op in ('LOAD', 'STORE'):
        if len(args) != 2:
            raise ValueError(f"{op} требует 2 аргумента")
        base.update({
            'register': parse_register(args[0]),
            'address': args[1]
        })
    elif op in ('ADD', 'SUB'):
        if len(args) != 2:
            raise ValueError(f"{op} требует 2 аргумента")
        base.update({
            'reg1': parse_register(args[0]),
            'reg2': parse_register(args[1])
        })
    elif op == 'JMP':
        if len(args) != 1:
            raise ValueError("JMP требует 1 аргумент")
        base['address'] = args[0]
    elif op == 'JZ':
        if len(args) != 2:
            raise ValueError("JZ требует 2 аргумента")
        base.update({
            'register': parse_register(args[0]),
            'address': args[1]
        })
    elif op == 'HALT':
        if args:
            raise ValueError("HALT не принимает аргументов")
    return base
def encode_instruction(instr: dict) -> bytes:
    opcode = instr['opcode']
    if opcode == OPCODES['HALT']:  # HALT
        return bytes([opcode << 4])
    elif opcode in (OPCODES['ADD'], OPCODES['SUB']):  # ADD, SUB
        reg1 = instr['reg1']
        reg2 = instr['reg2']
        return bytes([(opcode << 4) | (reg1 << 2) | reg2])
    elif opcode in (OPCODES['LOAD'], OPCODES['STORE'], OPCODES['JZ']):  # LOAD, STORE, JZ
        register = instr['register']
        address = instr['address']
        if not 0 <= address <= 0xFF:
            raise ValueError(f"Адрес вне диапазона [0-255]: {address}")
        return bytes([(opcode << 4) | register, address])
    elif opcode == OPCODES['JMP']:
        address = instr['address']
        if not 0 <= address <= 0xFF:
            raise ValueError(f"Адрес вне диапазона [0-255]: {address}")
        return bytes([opcode << 4, address])
    else:
        raise ValueError(f"Неизвестный опкод: {opcode}")
def format_bytes_for_test(binary_data: bytes) -> str:
    return ' '.join(f'{b:02X}' for b in binary_data)
def main():
    parser = argparse.ArgumentParser(description='Ассемблер для УВМ')
    parser.add_argument('input', help='Путь к исходному YAML-файлу')
    parser.add_argument('output', help='Путь к выходному бинарному файлу')
    parser.add_argument('--test', action='store_true',
                        help='Режим тестирования: вывод внутреннего представления')
    args = parser.parse_args()
    try:
        with open(args.input) as f:
            program = yaml.safe_load(f)
        ir = [translate_instruction(instr) for instr in program]
        if args.test:
            json.dump(ir, sys.stdout, indent=2)
            sys.stdout.write('\n\n')
            binary_data = b''
            for i, instr in enumerate(ir):
                instr_bytes = encode_instruction(instr)
                binary_data += instr_bytes
                print(f"Инструкция {i}: {format_bytes_for_test(instr_bytes)}")
            print(f"\nПолный вывод: {format_bytes_for_test(binary_data)}")
        else:
            binary_data = b''
            for instr in ir:
                binary_data += encode_instruction(instr)
            with open(args.output, 'wb') as bin_file:
                bin_file.write(binary_data)
            file_size = len(binary_data)
            print(f"Размер двоичного файла: {file_size} байт(а)")
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__':
    main()