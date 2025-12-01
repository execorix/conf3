import argparse
import sys
import csv

# --- КОНСТАНТЫ (должны совпадать с ассемблером) ---
OPCODES = {
    0x2: 'NEQ', 0x6: 'STORE', 0x9: 'LDI', 0xC: 'LOAD'
}
INSTRUCTION_SIZE = 5
REG_COUNT = 16
MEMORY_SIZE = 2 ** 20  # 1 Мегабайт ячеек


class VirtualMachine:
    def __init__(self):
        self.data_memory = [0] * MEMORY_SIZE  # Память данных
        self.registers = [0] * REG_COUNT  # Регистры R0-R15
        self.instruction_memory = b''  # Память команд
        self.pc = 0  # Program Counter

    def load_program(self, binary_path):
        """Загрузка бинарного кода."""
        with open(binary_path, 'rb') as f:
            self.instruction_memory = f.read()

    def run_cycle(self):
        """Основной цикл интерпретации."""

        # Инициализация для теста копирования массива (Требование 6)
        # Исходные данные: Mem[100]=50, Mem[101]=60, Mem[102]=70
        self.data_memory[100] = 50
        self.data_memory[101] = 60
        self.data_memory[102] = 70

        while self.pc < len(self.instruction_memory):
            # 1. FETCH и DECODE
            instr_bytes = self.instruction_memory[self.pc: self.pc + INSTRUCTION_SIZE]
            if len(instr_bytes) != INSTRUCTION_SIZE: break

            instruction = int.from_bytes(instr_bytes, byteorder='big')
            opcode = instruction & 0xF

            if opcode not in OPCODES:
                raise ValueError(f"Неизвестный опкод 0x{opcode:X} при PC={self.pc}")

            op_name = OPCODES[opcode]

            # 2. EXECUTE

            if op_name == 'LDI':
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

    def _execute_LDI(self, target_reg, value):
        self.registers[target_reg] = value

    def _execute_LOAD(self, target_reg, source_addr):
        self.registers[target_reg] = self.data_memory[source_addr]

    def _execute_STORE(self, target_addr, source_reg):
        self.data_memory[target_addr] = self.registers[source_reg]

    def _execute_NEQ(self, target_reg, source_addr):
        mem_value = self.data_memory[source_addr]
        reg_value = self.registers[target_reg]
        result = 1 if reg_value != mem_value else 0
        self.registers[target_reg] = result

    def dump_memory(self, path, start, end):
        """Дамп памяти в CSV."""
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Address", "Value"])
            limit = min(end + 1, len(self.data_memory))
            for i in range(start, limit):
                writer.writerow([i, self.data_memory[i]])


def main_interpreter():
    parser = argparse.ArgumentParser(description='Интерпретатор УВМ (Этап 3)')
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