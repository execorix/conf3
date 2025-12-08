import argparse
import sys
import csv
import os

OPCODES = {
    0x0: 'NOP',
    0x2: 'NEQ', 0x3: 'ADD', 0x4: 'SUB', 0x5: 'JMP', 0x6: 'JZ',
    0x7: 'IN', 0x8: 'OUT', 0x9: 'LDI', 0xA: 'STORE', 0xC: 'LOAD'
}
INSTRUCTION_SIZE = 5
MEMORY_SIZE = 2 ** 20


class VirtualMachine:
    def __init__(self, input_file=None):
        self.data_memory = [0] * MEMORY_SIZE
        self.registers = [0] * 16
        self.instruction_memory = b''
        self.pc = 0
        self.input_data = []
        if input_file:
            try:
                with open(input_file, 'r') as f:
                    self.input_data = [int(line.strip()) for line in f if line.strip()]
            except FileNotFoundError:
                print(f"Внимание: Файл ввода {input_file} не найден. Используется пустой буфер.", file=sys.stderr)

        self.input_ptr = 0
        self.output_log = []

    def load_program(self, binary_path):
        with open(binary_path, 'rb') as f:
            self.instruction_memory = f.read()

    def dump_memory(self, path, start, end):
        with open(path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for i in range(start, end):
                writer.writerow([i, self.data_memory[i]])

    def _execute_IN(self, target_reg, io_code):
        if self.input_ptr < len(self.input_data):
            value = self.input_data[self.input_ptr]
            self.registers[target_reg] = value
            self.input_ptr += 1
            print(f"[I/O] IN: R{target_reg} = {value} (Code: {io_code})")
        else:
            self.registers[target_reg] = 0
            print("[I/O] IN: Буфер пуст (EOF). R[C] = 0.")

    def _execute_OUT(self, source_reg, io_code):
        value = self.registers[source_reg]
        self.output_log.append((value, io_code))
        print(f"[I/O] OUT: Значение {value} (R{source_reg}) выведено с кодом {io_code}")

    def _execute_LDI(self, target_reg, value):
        self.registers[target_reg] = value

    def _execute_LOAD(self, target_reg, addr):
        self.registers[target_reg] = self.data_memory[addr]

    def _execute_STORE(self, addr, source_reg):
        self.data_memory[addr] = self.registers[source_reg]

    def _execute_ALU(self, op_type, target_reg, source_reg):
        val_b = self.registers[target_reg]
        val_c = self.registers[source_reg]

        if op_type == 'ADD':
            result = val_b + val_c
        elif op_type == 'SUB':
            result = val_b - val_c

        self.registers[target_reg] = result

    # --- ИСПРАВЛЕННАЯ ЛОГИКА NEQ (Логическая операция) ---
    def _execute_NEQ(self, target_reg, addr):
        val_reg = self.registers[target_reg]
        val_mem = self.data_memory[addr]
        # Если значения не равны, записываем 1 в регистр, иначе 0.
        self.registers[target_reg] = 1 if val_reg != val_mem else 0

    def run_cycle(self):
        while self.pc < len(self.instruction_memory):
            instr_bytes = self.instruction_memory[self.pc: self.pc + INSTRUCTION_SIZE]
            if len(instr_bytes) != INSTRUCTION_SIZE: break

            instruction = int.from_bytes(instr_bytes, byteorder='big')
            opcode = instruction & 0xF

            if opcode not in OPCODES:
                raise ValueError(f"Неизвестный опкод 0x{opcode:X} при PC={self.pc}")

            op_name = OPCODES[opcode]

            next_pc = self.pc + INSTRUCTION_SIZE

            if op_name == 'NOP':
                pass

            elif op_name == 'JMP':
                B_addr = (instruction >> 4)
                next_pc = B_addr
            elif op_name == 'JZ':
                B_reg = (instruction >> 4) & 0xF
                C_addr = (instruction >> 8) & 0x7FFFFFFF
                if self.registers[B_reg] == 0:
                    next_pc = C_addr

            elif op_name in ('IN', 'OUT', 'LDI'):
                C_reg = (instruction >> 30) & 0xF
                B_const = (instruction >> 4) & 0x3FFFFFF
                if op_name == 'IN':
                    self._execute_IN(C_reg, B_const)
                elif op_name == 'OUT':
                    self._execute_OUT(C_reg, B_const)
                elif op_name == 'LDI':
                    self._execute_LDI(C_reg, B_const)

            elif op_name == 'STORE':
                C_reg = (instruction >> 35) & 0xF
                B_addr = (instruction >> 4) & 0x7FFFFFFF
                self._execute_STORE(B_addr, C_reg)

            elif op_name in ('ADD', 'SUB'):
                B_reg = (instruction >> 4) & 0xF
                C_reg = (instruction >> 8) & 0xF
                self._execute_ALU(op_name, B_reg, C_reg)

            elif op_name == 'LOAD':
                C_addr = (instruction >> 8) & 0x7FFFFFFF
                B_reg = (instruction >> 4) & 0xF
                self._execute_LOAD(B_reg, C_addr)

            # --- ИСПРАВЛЕННЫЙ NEQ (Вызов логической операции) ---
            elif op_name == 'NEQ':
                C_addr = (instruction >> 8) & 0x7FFFFFFF
                B_reg = (instruction >> 4) & 0xF
                self._execute_NEQ(B_reg, C_addr)

            self.pc = next_pc


def main_interpreter():
    parser = argparse.ArgumentParser(description='Интерпретатор УВМ (Финальный)')
    parser.add_argument('binary', help='Путь к бинарному файлу с программой')
    parser.add_argument('result', help='Путь к файлу-дампу памяти (CSV)')
    parser.add_argument('range', help='Диапазон адресов памяти для дампа (например, 0:100)')
    parser.add_argument('--input', help='Путь к текстовому файлу с входными данными', default=None)

    args = parser.parse_args()
    try:
        start, end = map(int, args.range.split(':'))
    except ValueError:
        print("Ошибка: Неверный формат диапазона. Используйте, например, '0:50'.", file=sys.stderr)
        sys.exit(1)

    vm = VirtualMachine(input_file=args.input)
    vm.load_program(args.binary)

    try:
        vm.run_cycle()
        vm.dump_memory(args.result, start, end)
        print(f"\nВыполнение завершено. Дамп памяти сохранен в {args.result}")
        print(f"Состояние регистров R0-R3: {vm.registers[0:4]}...")

        print("\n--- I/O Вывод (Output Log) ---")
        if vm.output_log:
            for value, code in vm.output_log:
                print(f"[{code}]: {value}")
        else:
            print("Нет операций OUT.")

    except Exception as e:
        print(f"Ошибка времени выполнения: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main_interpreter()