import pandas as pd
from sqlalchemy import create_engine

# Путь к вашему CSV файлу
csv_file_path = r'.\data\processed_data\updated_file.csv'

# Загрузка данных из CSV
df = pd.read_csv(csv_file_path)

# Настройка подключения к базе данных SQLite
engine = create_engine('sqlite:///data/database/mydatabase.db')  

# Загрузка данных в таблицу (например, "pdf_analysis")
df.to_sql('pdf_analysis', con=engine, if_exists='replace', index=False)

print("Данные успешно загружены в базу данных SQLite!")
