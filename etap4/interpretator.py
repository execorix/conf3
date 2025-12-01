import argparse
import sys
import csv

OPCODES = {
    0x2: 'NEQ', 0x3: 'ADD', 0x4: 'SUB', 0x5: 'JMP', 0x6: 'JZ', 0x9: 'LDI', 0xC: 'LOAD'
}
INSTRUCTION_SIZE = 5
MEMORY_SIZE = 2 ** 20


class VirtualMachine:
    def __init__(self):
        self.data_memory = [0] * MEMORY_SIZE
        self.registers = [0] * 16  # R0-R15
        self.instruction_memory = b''
        self.pc = 0

    def load_program(self, binary_path):
        with open(binary_path, 'rb') as f:
            self.instruction_memory = f.read()

    def run_cycle(self):
        # Инициализация для теста (R1=10, R2=5, Mem[50]=0)
        self.registers[1] = 10
        self.registers[2] = 5
        self.data_memory[50] = 0

        while self.pc < len(self.instruction_memory):
            instr_bytes = self.instruction_memory[self.pc: self.pc + INSTRUCTION_SIZE]
            if len(instr_bytes) != INSTRUCTION_SIZE: break

            instruction = int.from_bytes(instr_bytes, byteorder='big')
            opcode = instruction & 0xF

            if opcode not in OPCODES:
                raise ValueError(f"Неизвестный опкод 0x{opcode:X} при PC={self.pc}")

            op_name = OPCODES[opcode]

            if op_name == 'JMP':
                # A (0-3), B (4-39, Адрес)
                B_addr = (instruction >> 4)
                self.pc = B_addr
                continue

            elif op_name == 'JZ':
                B_reg = (instruction >> 4) & 0xF
                C_addr = (instruction >> 8) & 0x7FFFFFFF
                if self.registers[B_reg] == 0:
                    self.pc = C_addr  # Условный переход
                    continue
            if op_name == 'ADD':
                B_reg = (instruction >> 4) & 0xF
                C_reg = (instruction >> 8) & 0xF
                self._execute_ALU('ADD', B_reg, C_reg)

            elif op_name == 'SUB':
                B_reg = (instruction >> 4) & 0xF
                C_reg = (instruction >> 8) & 0xF
                self._execute_ALU('SUB', B_reg, C_reg)

            elif op_name == 'LDI':
                C_reg = (instruction >> 30) & 0xF
                B_const = (instruction >> 4) & 0x3FFFFFF
                self._execute_LDI(C_reg, B_const)

            elif op_name == 'LOAD':
                C_addr = (instruction >> 8) & 0x7FFFFFFF
                B_reg = (instruction >> 4) & 0xF
                self._execute_LOAD(B_reg, C_addr)

            elif op_name == 'STORE':
                C_reg = (instruction >> 35) & 0xF
                B_addr = (instruction >> 4) & 0x7FFFFFFF
                self._execute_STORE(B_addr, C_reg)

            elif op_name == 'NEQ':
                C_addr = (instruction >> 8) & 0x7FFFFFFF
                B_reg = (instruction >> 4) & 0xF
                self._execute_NEQ(B_reg, C_addr)

            self.pc += INSTRUCTION_SIZE
    def _execute_ALU(self, op, reg_b, reg_c):
        """ADD/SUB: R[B] = R[B] op R[C]"""
        val_b = self.registers[reg_b]
        val_c = self.registers[reg_c]

        if op == 'ADD':
            self.registers[reg_b] = val_b + val_c
        elif op == 'SUB':
            self.registers[reg_b] = val_b - val_c

    def _execute_LDI(self, target_reg, value):
        self.registers[target_reg] = value

    def _execute_LOAD(self, target_reg, source_addr):
        self.registers[target_reg] = self.data_memory[source_addr]

    def _execute_STORE(self, target_addr, source_reg):
        self.data_memory[target_addr] = self.registers[source_reg]

    def _execute_NEQ(self, target_reg, source_addr):
        mem_value = self.data_memory[source_addr]
        reg_value = self.registers[target_reg]
        self.registers[target_reg] = 1 if reg_value != mem_value else 0

    def dump_memory(self, path, start, end):
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Address", "Value"])
            limit = min(end + 1, len(self.data_memory))
            for i in range(start, limit):
                writer.writerow([i, self.data_memory[i]])


def main_interpreter():
    parser = argparse.ArgumentParser(description='Интерпретатор УВМ (Этап 4)')
    parser.add_argument('binary', help='Путь к бинарному файлу с программой')
    parser.add_argument('result', help='Путь к файлу-дампу памяти (CSV)')
    parser.add_argument('range', help='Диапазон адресов памяти для дампа (например, 0:100)')
    args = parser.parse_args()
    start, end = map(int, args.range.split(':'))
    vm = VirtualMachine()
    vm.load_program(args.binary)
    try:
        vm.run_cycle()
        vm.dump_memory(args.result, start, end)
        print(f"Выполнение завершено. Дамп памяти сохранен в {args.result}")
        print(f"Состояние регистров R0-R3: {vm.registers[0:4]}...")
    except Exception as e:
        print(f"Ошибка времени выполнения: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main_interpreter()