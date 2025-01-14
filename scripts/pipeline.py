import subprocess
import argparse
import os

VENV_PYTHON = "C:/Users/German/VSCodeProjects/ITMO_DE/venv/Scripts/python.exe"

def run_script(script_path, name):
    print(f"Запускается {name}...")
    result = subprocess.run([VENV_PYTHON, script_path], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Ошибка в {name}: {result.stderr}")
    else:
        print(f"{name} завершён.")

def run_dashboard():
    print("Запускается dashboard.py...")
    subprocess.Popen([VENV_PYTHON, "scripts/dashboard.py"])
    print("Дашборд запущен. Перейдите по ссылке: http://localhost:8050")

def main():
    parser = argparse.ArgumentParser(description="Pipeline CLI для выполнения скриптов.")
    parser.add_argument(
        "step",
        choices=["preprocess", "test", "create_db", "dashboard", "llm", "all"],
        help="Выберите шаг для выполнения или 'all' для выполнения всех шагов последовательно.",
    )
    parser.add_argument(
        "--openai_key",
        type=str,
        help="API ключ для OpenAI. Если указан, выполняется полный набор шагов.",
    )
    args = parser.parse_args()

    if args.step == "preprocess":
        run_script("scripts/preprocess.py", "Preprocess")
    elif args.step == "test":
        run_script("scripts/llm_annotate.py", "Llm_annotate")
    elif args.step == "create_db":
        run_script("scripts/create_db.py", "Create DB")
    elif args.step == "dashboard":
        run_dashboard()
    elif args.step == "all":
        if args.openai_key:
            os.environ["OPENAI_API_KEY"] = args.openai_key  # Устанавливаем ключ в переменную окружения
            run_script("scripts/preprocess.py", "Preprocess")
            run_script("scripts\llm_annotate.py", "Llm_annotate")
            run_script("scripts/create_db.py", "Create DB")
            run_dashboard()
        else:
            print("OpenAI API ключ не указан.")
            run_script("scripts/preprocess.py", "Preprocess")
            run_script("scripts/test.py", "Test")
            run_script("scripts/create_db.py", "Create DB")
            run_dashboard()

if __name__ == "__main__":
    main()
