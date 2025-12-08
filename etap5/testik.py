import subprocess
import os
import sys

# Список файлов для тестирования
TEST_PROGRAMS = [
    ("vector_neq.yaml", "input_vec.txt", "10:30"),  # R1: Требование 1
    ("example_1_arithmetic.yaml", "input_arith.txt", "0:5"),  # R2: Пример 1
    ("example_2_conditional.yaml", None, "48:52")  # R2: Пример 2
]


def run_test(program_file, input_file, dump_range):
    """Сборка и выполнение одной программы УВМ."""
    base_name = os.path.splitext(program_file)[0]
    binary_file = f"{base_name}.bin"
    dump_file = f"{base_name}_dump.csv"

    print(f"\n--- {base_name}: 1. Сборка ---")
    try:
        subprocess.run([sys.executable, "assembler.py", program_file, binary_file], check=True,
                       stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError:
        print(f"❌ Ошибка сборки {program_file}.", file=sys.stderr)
        return

    print(f"--- {base_name}: 2. Выполнение ---")
    interpreter_command = [sys.executable, "interpreter.py", binary_file, dump_file, dump_range]
    if input_file:
        interpreter_command.extend(["--input", input_file])

    try:
        subprocess.run(interpreter_command, check=True, stdout=sys.stdout, stderr=sys.stderr)
        print(f"Тест {program_file} успешно завершен. Результат в {dump_file}")
    except subprocess.CalledProcessError:
        print(f"Ошибка выполнения {program_file}.", file=sys.stderr)


def create_input_files():
    with open("input_arith.txt", "w") as f:
        f.write("70\n")
    print("Создан файл ввода: input_arith.txt")
    with open("input_vec.txt", "w") as f:
        f.write("1\n2\n3\n4\n5\n6\n7\n1\n9\n3\n9\n5\n9\n7\n")
    print("Создан файл ввода: input_vec.txt")


if __name__ == '__main__':
    create_input_files()
    program_1_content = globals()['vector_neq.yaml']
    program_2_content = globals()['example_1_arithmetic.yaml']
    program_3_content = globals()['example_2_conditional.yaml']

    with open("vector_neq.yaml", "w") as f:
        f.write(program_1_content)
    with open("example_1_arithmetic.yaml", "w") as f:
        f.write(program_2_content)
    with open("example_2_conditional.yaml", "w") as f:
        f.write(program_3_content)
    print("\n===== ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ УВМ =====")
    for program, input_f, dump_r in TEST_PROGRAMS:
        run_test(program, input_f, dump_r)