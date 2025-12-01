import argparse
import json
import sys
import yaml  # Используется для чтения JSON/YAML

OPCODES = {
    'NEQ': 0x2,
    'STORE': 0x6,
    'LDI': 0x9,
    'LOAD': 0xC
}
MAX_REG_ADDR = 0xF  # 4 бита (0-15)
MAX_MEM_ADDR_31 = 0x7FFFFFFF  # 31 бит
MAX_CONST_26 = 0x3FFFFFF  # 26 бит


def parse_register(reg: str) -> int:
    if not reg.startswith('R') or not reg[1:].isdigit():
        raise ValueError(f"Некорректный регистр: {reg}")
    reg_idx = int(reg[1:])
    if not 0 <= reg_idx <= MAX_REG_ADDR:
        raise ValueError(f"Регистр вне диапазона [R0-R{MAX_REG_ADDR}]: {reg}")
    return reg_idx


def translate_instruction(instr: dict) -> dict:
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

    elif op == 'LOAD':  # A=12, B=Регистр (4b), C=Адрес (31b)
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
        base['fields'] = {'B_addr': addr, 'C_reg': source_reg}

    elif op == 'NEQ':
        target_reg = parse_register(instr['target_reg'])
        addr = instr['addr']
        if not 0 <= addr <= MAX_MEM_ADDR_31:
            raise ValueError(f"Адрес {addr} вне диапазона (0-{MAX_MEM_ADDR_31})")
        base['fields'] = {'B_reg': target_reg, 'C_addr': addr}

    return base


def main_assembler_stage1():
    parser = argparse.ArgumentParser(description='Ассемблер УВМ (Этап 1: IR)')
    parser.add_argument('input', help='Путь к исходному JSON/YAML-файлу')
    parser.add_argument('output', help='Путь к выходному бинарному файлу (игнорируется на этом этапе)')
    parser.add_argument('--test', action='store_true',
                        help='Режим тестирования: вывод внутреннего представления')
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            program = yaml.safe_load(f)
        ir = [translate_instruction(instr) for instr in program]

        if args.test:
            print("--- Внутреннее представление (IR) программы ---")
            for i, instr in enumerate(ir):
                print(f"Инструкция {i} ({instr['op']}):")
                print(f"  Opcode (A): {instr['opcode']}")

                if instr['op'] == 'LDI':
                    print(f"  Поле B (Константа): {instr['fields']['B_const']}")
                    print(f"  Поле C (Регистр): {instr['fields']['C_reg']}")
                elif instr['op'] == 'LOAD' or instr['op'] == 'NEQ':
                    print(f"  Поле B (Регистр): {instr['fields']['B_reg']}")
                    print(f"  Поле C (Адрес): {instr['fields']['C_addr']}")
                elif instr['op'] == 'STORE':
                    print(f"  Поле B (Адрес): {instr['fields']['B_addr']}")
                    print(f"  Поле C (Регистр): {instr['fields']['C_reg']}")

        else:
            print("Этап 1 завершен. Программа транслирована во внутреннее представление (IR).")

    except Exception as e:
        print(f"Ошибка Этапа 1: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main_assembler_stage1()