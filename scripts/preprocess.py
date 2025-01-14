# preprocess.py
import os
import re
from datetime import datetime
import json
import pandas as pd
from PyPDF2 import PdfReader
import fitz
import pdfplumber
from pdf2image import convert_from_path
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer

# 1. Проверка PDF файлов

def check_pdf_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            try:
                path = os.path.join(directory, filename)
                PdfReader(path)  # Пробуем открыть файл
                print(f"{filename}: OK")
            except Exception as e:
                print(f"{filename}: Error - {e}")

# 2. Проверка пустых слайдов

def check_empty_slides(directory):
    empty_slides = []
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            path = os.path.join(directory, filename)
            doc = fitz.open(path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if not text.strip():
                    empty_slides.append((filename, page_num + 1))

    if empty_slides:
        print("\nПустые слайды:")
        for slide in empty_slides:
            print(f"Файл: {slide[0]}, Слайд: {slide[1]}")
    else:
        print("\nПустых слайдов не найдено.")

# 3. Проверка страниц с изображениями без текста

def check_image_only_pages(directory):
    image_only_pages = []
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            path = os.path.join(directory, filename)
            doc = fitz.open(path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                if not text.strip() and len(page.get_images(full=True)) > 0:
                    image_only_pages.append((filename, page_num + 1))

    if image_only_pages:
        print("\nСтраницы с изображениями, без текста:")
        for page in image_only_pages:
            print(f"Файл: {page[0]}, Слайд: {page[1]}")
    else:
        print("\nНет страниц с изображениями без текста.")

# 4. Генерация отчета об очистке

def generate_clean_report(directory):
    report = []
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            path = os.path.join(directory, filename)
            doc = fitz.open(path)
            file_report = {"file": filename, "empty_pages": []}

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if not text.strip():
                    file_report["empty_pages"].append(page_num + 1)

            if file_report["empty_pages"]:
                report.append(file_report)
    print(report)
    with open("cleaning_report.json", "w") as f:
        json.dump(report, f, indent=4)

# 5. Переименование файлов

def rename_presentation_files(directory):
    for i, filename in enumerate(os.listdir(directory)):
        if filename.endswith(".pdf"):
            old_path = os.path.join(directory, filename)

            base_name = os.path.splitext(filename)[0]
            new_base_name = re.sub(r'[\W]', '', base_name).replace(" ", "_").lower()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{i}.pdf"

            new_path = os.path.join(directory, new_name)
            os.rename(old_path, new_path)
            print(f"Файл '{filename}' переименован в '{new_name}'")

# 6. Извлечение данных из PDF

def clean_table(table):
    return [
        [value for value in row if value not in (None, '')]
        for row in table
        if any(value not in (None, '') for value in row)
    ]

def extract_pdf_data(pdf_path):
    doc = fitz.open(pdf_path)
    total_images = 0
    fonts = set()
    text_content = []
    title_count = 0

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        total_images += len(page.get_images(full=True))
        text = page.get_text()
        text_content.append(text)
        for block in page.get_text("dict")["blocks"]:
            if block["type"] == 0:  # Текстовые блоки
                for line in block["lines"]:
                    for span in line["spans"]:
                        fonts.add(span["font"])
                        if span["size"] > 18:  # Заголовки (шрифт > 18)
                            title_count += 1

    total_tables = 0
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    cleaned_table = [
                        [value for value in row if value not in (None, '')]
                        for row in table
                        if any(value not in (None, '') for value in row)
                    ]
                    if cleaned_table:
                        total_tables += 1

    # Анализ текста
    all_text = " ".join(text_content)
    vectorizer = CountVectorizer(max_features=5, stop_words='english')
    keywords = vectorizer.fit_transform([all_text])
    feature_names = vectorizer.get_feature_names_out()
    keyword_list = ", ".join(feature_names)

    # Определение плотности текста
    text_density = len(all_text) / (doc.page_count * 792 * 612)  # Площадь стандартной страницы (A4)

    # Определение цветовой палитры (предполагается, что используется только fitz)
    color_palette = Counter()
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        for block in page.get_drawings():  # Рисунки и элементы на странице
            if "colors" in block:  # Проверяем, содержит ли блок информацию о цветах
                for color in block["colors"]:
                    color_palette[color] += 1

    most_common_colors = [color[0] for color in color_palette.most_common(3)]

    return {
        "font": ', '.join(fonts),
        "images_count": total_images,
        "tables_count": total_tables,
        "Design": "not defined",
        "Style": "not defined",
        "language": "English",
        "Slides_count": doc.page_count,
        "Text_density": text_density,
        "Keywords": keyword_list,
        "Color_palette": ", ".join(most_common_colors),
        "Title_density": title_count / doc.page_count * 100  # В процентах
    }

def process_pdf_files(directory_path):
    all_data = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory_path, filename)
            print(f"Обработка: {filename}")
            data = extract_pdf_data(pdf_path)
            data["PDF-name"] = filename
            all_data.append(data)

    df = pd.DataFrame(all_data)
    df.to_csv("pdf_analysis_output.csv", index=False)

# Основной скрипт
if __name__ == "__main__":
    raw_path = "./data/raw_data"
    check_pdf_files(raw_path)
    check_empty_slides(raw_path)
    check_image_only_pages(raw_path)
    generate_clean_report(raw_path)
    rename_presentation_files(raw_path)
    process_pdf_files(raw_path)
