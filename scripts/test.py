import csv


if __name__ == "__main__":
    # Путь к PDF файлу
    folder_path = 'data/processed_data'
    

    # Анализ PDF файла через OpenAI
    analysis_results = [
    {
        "filename": "2426hg2rxrznrhx3yhordf5c57ppaahe11_20250112_154602_20250112_174144_20250112_174258.pdf",
        "analysis": {
            "design": "minimalistic1",
            "style": "general1"
        }
    },
    {
        "filename": "2426hg2rxrznrhx3yhordf5c57ppaahe1_20250112_154602_20250112_174144_20250112_174258.pdf",
        "analysis": {
            "design": "minimalistic2",
            "style": "general2"
        }
    },
    {
        "filename": "25oof5wzsj4m6jg3bpydo56gybr65wet_20250112_154602_20250112_174144_20250112_174258.pdf",
        "analysis": {
            "design": "bright3",
            "style": "formal3"
        }
    }
]


    csv_file_path = 'pdf_analysis_output.csv'
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        
    analysis_dict = {result['filename']: result['analysis'] for result in analysis_results}

    # Обновляем строки CSV с новыми данными
    for row in rows:
        filename = row["PDF-name"]
        
        # Ищем соответствующий анализ для текущего файла
        if filename in analysis_dict:
            analysis = analysis_dict[filename]
            
            # Вставляем данные в соответствующие столбцы
            row["Design"] = analysis["design"]
            row["Style"] = analysis["style"]
    output_csv_path = 'data/processed_data/updated_file.csv'
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())  # Используем заголовки из первой строки
        writer.writeheader()
        writer.writerows(rows)