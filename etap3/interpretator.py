import argparse
import sys
from typing import Dict, Any, List, Optional
import struct

OPCODES = {
    'NOP': 0x0, 'NEQ': 0x2, 'ADD': 0x3, 'JMP': 0x5, 'JZ': 0x6,
    'STORE': 0x6, 'LDI': 0x9, 'LOAD': 0xC
}
MAX_REG_ADDR = 0xF
MAX_CONST_26 = 0x3FFFFFF
MAX_ADDR_31 = 0x7FFFFFFF
INSTRUCTION_SIZE = 5
DATA_MEMORY_SIZE = 4096
class UVMState:
    def __init__(self):
        self.data_memory = [0] * DATA_MEMORY_SIZE
        self.registers = [0] * (MAX_REG_ADDR + 1)
        self.pc = 0
    def get_reg(self, addr: int) -> int:
        if not 0 <= addr <= MAX_REG_ADDR:
            raise ValueError(f"Неверный адрес регистра: R{addr}")
        return self.registers[addr]
    def set_reg(self, addr: int, value: int):
        if not 0 <= addr <= MAX_REG_ADDR:
            raise ValueError(f"Неверный адрес регистра: R{addr}")
        value &= 0xFFFFFFFF
        if addr != 0:
            self.registers[addr] = value
        else:
            self.registers[0] = 0
    def get_data(self, addr: int) -> int:
        if not 0 <= addr < DATA_MEMORY_SIZE:
            raise ValueError(f"Обращение к памяти данных вне диапазона: {addr}")
        return self.data_memory[addr]

    def set_data(self, addr: int, value: int):
        if not 0 <= addr < DATA_MEMORY_SIZE:
            raise ValueError(f"Обращение к памяти данных вне диапазона: {addr}")
        self.data_memory[addr] = value & 0xFFFFFFFF
def disassamble_instruction(instr_bytes: bytes) -> Dict[str, Any]:
    if len(instr_bytes) != INSTRUCTION_SIZE:
        raise ValueError(f"Неверный размер команды: ожидалось {INSTRUCTION_SIZE}, получено {len(instr_bytes)}")
    instr_word = int.from_bytes(instr_bytes, byteorder='little')
    opcode = instr_word & 0xF
    op_name = next((name for name, code in OPCODES.items() if code == opcode), None)
    if not op_name:
        raise ValueError(f"Неизвестный Opcode: 0x{opcode:X}")
    base = {'op': op_name, 'opcode': opcode, 'fields': {}}
    if op_name == 'LDI':
        base['fields']['B_const'] = (instr_word >> 4) & MAX_CONST_26
        base['fields']['C_reg'] = (instr_word >> 30) & MAX_REG_ADDR
    elif op_name in ('LOAD', 'NEQ', 'JZ'):
        base['fields']['B_reg'] = (instr_word >> 4) & MAX_REG_ADDR
        base['fields']['C_addr'] = (instr_word >> 8) & MAX_ADDR_31
    elif op_name == 'STORE':
        base['fields']['B_addr'] = (instr_word >> 4) & MAX_ADDR_31
        base['fields']['C_reg'] = (instr_word >> 35) & MAX_REG_ADDR
    elif op_name == 'ADD':
        base['fields']['B_reg'] = (instr_word >> 4) & MAX_REG_ADDR
        base['fields']['C_reg'] = (instr_word >> 8) & MAX_REG_ADDR
    elif op_name == 'JMP':
        base['fields']['B_addr'] = (instr_word >> 4) & MAX_ADDR_31
    return base
def execute_instruction(ir_instr: Dict[str, Any], state: UVMState):
    op = ir_instr['op']
    fields = ir_instr['fields']
    next_pc = state.pc + 1
    if op == 'LDI':
        state.set_reg(fields['C_reg'], fields['B_const'])
    elif op == 'LOAD':
        data = state.get_data(fields['C_addr'])
        state.set_reg(fields['B_reg'], data)
    elif op == 'STORE':
        data = state.get_reg(fields['C_reg'])
        state.set_data(fields['B_addr'], data)
    elif op == 'ADD':
        reg_b = fields['B_reg']
        val_b = state.get_reg(reg_b)
        val_c = state.get_reg(fields['C_reg'])
        state.set_reg(reg_b, val_b + val_c)
    elif op == 'JMP':
        next_pc = fields['B_addr']
    elif op == 'JZ':
        if state.get_reg(fields['B_reg']) == 0:
            next_pc = fields['C_addr']
    elif op == 'NEQ':
        reg_b = fields['B_reg']
        val_b = state.get_reg(reg_b)
        val_c = state.get_data(fields['C_addr'])
        state.set_reg(reg_b, 1 if val_b != val_c else 0)
    elif op == 'NOP':
        pass
    state.pc = next_pc
def run_simulator(instr_memory: bytes, state: UVMState, max_steps: int = 1000):
    total_instr_count = len(instr_memory) // INSTRUCTION_SIZE
    if len(instr_memory) % INSTRUCTION_SIZE != 0:
        raise ValueError("Размер бинарного файла не кратен размеру команды (5 байт).")
    print(f"Запуск симулятора. Команд в памяти: {total_instr_count}.")
    step = 0
    while 0 <= state.pc < total_instr_count and step < max_steps:
        start_byte = state.pc * INSTRUCTION_SIZE
        instr_bytes = instr_memory[start_byte: start_byte + INSTRUCTION_SIZE]
        ir_instr = disassamble_instruction(instr_bytes)
        execute_instruction(ir_instr, state)
        step += 1
    if step >= max_steps:
        print(f"Симулятор остановлен по достижении лимита шагов ({max_steps}).")
    elif state.pc >= total_instr_count:
        print(f"Программа завершена.")
    else:
        print(f"Симулятор остановлен.")
def dump_memory(state: UVMState, dump_path: str, start_addr: int, end_addr: int):
    if start_addr < 0 or end_addr >= DATA_MEMORY_SIZE or start_addr > end_addr:
        raise ValueError(f"Неверный диапазон адресов: [{start_addr}-{end_addr}].")
    print(f"Сохранение дампа памяти в {dump_path}...")
    with open(dump_path, 'w') as f:
        f.write("Address,Value\n")
        for addr in range(start_addr, end_addr + 1):
            value = state.data_memory[addr]
            f.write(f"0x{addr:04X},0x{value:08X}\n")
    print("✅ Дамп успешно сохранен.")
def main_simulator():
    parser = argparse.ArgumentParser(description='Симулятор УВМ (Этап 3)')
    parser.add_argument('binary', help='Путь к бинарному файлу с программой')
    parser.add_argument('dump_path', help='Путь к файлу для сохранения дампа памяти (CSV)')
    parser.add_argument('addr_range', help='Диапазон адресов для дампа, например: 0x0-0x10')
    args = parser.parse_args()
    try:
        start_hex, end_hex = args.addr_range.split('-')
        start_addr = int(start_hex, 16)
        end_addr = int(end_hex, 16)
    except Exception:
        print("Ошибка: Неверный формат диапазона адресов. Используйте 0xSTART-0xEND.", file=sys.stderr)
        sys.exit(1)
    try:
        with open(args.binary, 'rb') as f:
            instr_memory = f.read()
    except FileNotFoundError:
        print(f"Ошибка: Бинарный файл не найден: {args.binary}", file=sys.stderr)
        sys.exit(1)
    state = UVMState()
    SOURCE_ADDR = 0x100
    for i in range(5):
        state.set_data(SOURCE_ADDR + i, 0xAA00 + i)
    try:
        run_simulator(instr_memory, state)
        dump_memory(state, args.dump_path, start_addr, end_addr)
    except Exception as e:
        print(f"Критическая ошибка симуляции: {e}", file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__':
    main_simulator()