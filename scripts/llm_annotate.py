import os
import base64
import json
import csv
from pdf2image import convert_from_path
from dotenv import load_dotenv
from openai import OpenAI

# Загрузка переменных окружения
load_dotenv()

# Настройка OpenAI API
openai_api_key = os.getenv("OPENAI_KEY")
if not openai_api_key:
    raise ValueError("API ключ OpenAI не найден в переменных окружения.")

client = OpenAI(api_key=openai_api_key, base_url="https://api.vsegpt.ru/v1")

# Функция для кодирования изображения в base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Функция для конвертации PDF в изображения
def pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path, fmt='jpeg')  # Конвертируем в JPEG
    return images

# Функция для обработки первых трех страниц PDF файла и анализа через OpenAI
def analyze_pdf_with_openai(pdf_path):
    images = pdf_to_images(pdf_path)[:3]  # Берём только первые три страницы
    image_urls = []

    for i, image in enumerate(images):
        # Сохранение изображения во временный файл
        temp_image_path = f"{pdf_path}_page_{i+1}.jpg"
        image.save(temp_image_path, 'JPEG')

        # Кодирование изображения в base64
        base64_image = encode_image(temp_image_path)
        image_urls.append({
            "type": "image_url",
            "image_url": f"data:image/jpeg;base64,{base64_image}"
        })

        # Удаление временного файла
        os.remove(temp_image_path)

    # Запрос к OpenAI для анализа изображений
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": """Analyze these pages and return the design style and text style. 
                     The response should be structured strictly as a JSON object: {"design": "","style": ""} """},
                    *image_urls
                ]
            }
        ]
    )

    # Парсинг ответа
    response_content = response.choices[0]["message"]["content"]

    # Извлечение данных из ответа
    try:
        parsed_response = json.loads(response_content)
    except json.JSONDecodeError:
        raise ValueError(f"Не удалось преобразовать ответ LLM в JSON: {response_content}")

    return parsed_response

# Основной код
if __name__ == "__main__":
    # Путь к PDF файлу
    folder_path = 'data/processed_data'
    

    # Анализ PDF файла через OpenAI
    analysis_results = []
    for filename in os.listdir(folder_path):
        pdf_path = os.path.join(folder_path, filename)
        if pdf_path.endswith(".pdf"):
            try:
                # Анализ PDF файла через OpenAI
                analysis_result = analyze_pdf_with_openai(pdf_path)
                analysis_results.append({
                "filename": filename,
                "analysis": analysis_result
            })
            except Exception as e:
                print(f"Error processing {pdf_path}: {e}")

    csv_file_path = 'data/processed_data/your_existing_file.csv'
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        
    analysis_dict = {result['filename']: result['analysis'] for result in analysis_results}

    # Обновляем строки CSV с новыми данными
    for row in rows:
        filename = row["PDF файл"]
        
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