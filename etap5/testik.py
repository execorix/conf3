# run_uvm.py
import subprocess
import os
import sys


def run_test(program_file, input_file=None):
    base_name = os.path.splitext(program_file)[0]
    binary_file = f"{base_name}.bin"
    dump_file = f"{base_name}_dump.csv"
    print(f"\n--- 1. Сборка {program_file} ---")
    subprocess.run([sys.executable, "assembler.py", program_file, binary_file], check=True, stdout=sys.stdout,
                    stderr=sys.stderr)
    print(f"\n--- 2. Выполнение {binary_file} ---")
    interpreter_command = [sys.executable, "interpreter.py", binary_file, dump_file, "0:50"]
    if input_file:
        interpreter_command.extend(["--input", input_file])
    subprocess.run(interpreter_command, check=True, stdout=sys.stdout, stderr=sys.stderr)
    print(f"Тест {program_file} успешно завершен.")



def create_test_files():
    input_txt_content = "5\n15\n2\n"
    with open("input.txt", "w") as f:
        f.write(input_txt_content)
    print("Создан файл ввода: input.txt")
    final_test_json = """
[
    {"op": "IN", "target_reg": "R1", "value_code": 1},
    {"op": "IN", "target_reg": "R2", "value_code": 2},
    {"op": "ADD", "target_reg": "R1", "source_reg": "R2"}, 
    {"op": "NOP"},
    {"op": "IN", "target_reg": "R3", "value_code": 3},
    {"op": "ADD", "target_reg": "R1", "source_reg": "R3"},
    {"op": "OUT", "target_reg": "R1", "value_code": 10},
    {"op": "NOP"}
]
"""
    with open("final_test.json", "w") as f:
        f.write(final_test_json)
    print("Создан файл программы: final_test.json")


if __name__ == '__main__':
    create_test_files()
    print("\n===== ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ УВМ (ЭТАП 5) =====")
    run_test("final_test.json", "input.txt")