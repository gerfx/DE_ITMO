import dash
import dash_bootstrap_components as dbc
import sqlite3
import pandas as pd
import plotly.express as px

from dash import dcc, html, Input, Output


# Путь к базе данных
DB_PATH = r'data\database\mydatabase.db'

# Функция для выполнения запросов к базе данных
def fetch_data(query):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)
    
def calculate_data_quality_metrics(data):
    metrics = {
        "Полнота данных": (1 - data["title_density"].isnull().mean().mean()) * 100,
        "Уникальность данных": (
        sum(df.nunique().mean() for df in data.values() if isinstance(df, pd.DataFrame)) 
        / len(data)
    )
    }
    return pd.DataFrame(metrics.items(), columns=["Метрика", "Значение (%)"])


def parse_keywords(keywords_string):
    # Разделяем строку по запятой и удаляем лишние пробелы
    return [keyword.strip() for keyword in keywords_string.split(",")]

# Функция для парсинга значения шрифта и исключения стилей
def parse_font(font_string):
    # Разделяем строку по запятой и убираем пробелы
    font_components = [part.strip() for part in font_string.split(',')]
    
    # Список стилей, которые нужно исключить
    excluded_styles = ["Bold", "Italic", "BoldItalic", "Light", "Regular"]
    
    # Фильтруем компоненты шрифта, исключая нежелательные стили
    return [part for part in font_components if part not in excluded_styles]

# Инициализация Dash приложения
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout приложения
app.layout = html.Div([
    dbc.Container([
        html.H1("PDF Analysis Dashboard", className="text-center my-4"),
        
        # Графики и таблицы для разных отчетов
        dbc.Row([
            dbc.Col(dcc.Graph(id="design-distribution"), width=6),
            dbc.Col(dcc.Graph(id="font-distribution"), width=6),
        ]),
        
        dbc.Row([
            dbc.Col(dcc.Graph(id="images-count-distribution"), width=6),
            dbc.Col(dcc.Graph(id="tables-count-distribution"), width=6),
        ]),
        
        dbc.Row([
            dbc.Col(dcc.Graph(id="text-density-distribution"), width=6),
            dbc.Col(dcc.Graph(id="keywords-distribution"), width=6),
        ]),

        dcc.Graph(id="box-plot-distribution"), 
        dcc.Graph(id="heatmap-correlation"),
        html.Div(id="data-table", className="mt-4"),
        html.Div(id="data_quality_metrics", className="mt-4"),
    ])
])

# Callback для обновления данных в дашборде
@app.callback(
    Output("design-distribution", "figure"),
    Output("font-distribution", "figure"),
    Output("images-count-distribution", "figure"),
    Output("tables-count-distribution", "figure"),
    Output("text-density-distribution", "figure"),
    Output("keywords-distribution", "figure"),
    Output("data-table", "children"),
    Output("data_quality_metrics", "children"),
    Input("design-distribution", "id")  # Триггер (можно заменить на другой элемент)
)
def update_dashboard(_):
    # Данные для графиков
    data_queries = {
        "design": "SELECT Design, COUNT(*) as count FROM pdf_analysis GROUP BY Design;",
        "font": "SELECT font, COUNT(*) as count FROM pdf_analysis GROUP BY font;",
        "images_count": "SELECT images_count, COUNT(*) as count FROM pdf_analysis GROUP BY images_count;",
        "tables_count": "SELECT tables_count, COUNT(*) as count FROM pdf_analysis GROUP BY tables_count;",
        "title_density": "SELECT Title_density, COUNT(*) as count FROM pdf_analysis GROUP BY Title_density;",
        "keywords": "SELECT Keywords, COUNT(*) as count FROM pdf_analysis GROUP BY Keywords;",
    }
    
    # Получение данных для графиков
    data = {key: fetch_data(query) for key, query in data_queries.items()}
    
    # Парсим шрифты и исключаем нежелательные стили
    font_data = data["font"]["font"].apply(parse_font)
    
    # Разворачиваем все компоненты в одну строку (каждое значение шрифта)
    flattened_fonts = [item for sublist in font_data for item in sublist]
    
    # Создаем DataFrame для подсчета частоты каждого значения
    font_df = pd.DataFrame(flattened_fonts, columns=["font_component"])
    font_counts = font_df["font_component"].value_counts().reset_index()
    font_counts.columns = ["font_component", "count"]

    # Разбираем значения в столбце Keywords
    keyword_data = data["keywords"]["Keywords"].apply(parse_keywords)
    
    # Разворачиваем все ключевые слова в одну строку (каждое ключевое слово)
    flattened_keywords = [item for sublist in keyword_data for item in sublist]
    
    # Создаем DataFrame для подсчета частоты каждого ключевого слова
    keyword_df = pd.DataFrame(flattened_keywords, columns=["keyword"])
    keyword_counts = keyword_df["keyword"].value_counts().reset_index()
    keyword_counts.columns = ["keyword", "count"]

    # Графики
    fig_design = px.bar(data["design"], x="Design", y="count", title="Распределение по дизайну")
    fig_font = px.bar(font_counts, x="font_component", y="count", title="Распределение компонентов шрифта")
    fig_images_count = px.bar(data["images_count"], x="images_count", y="count", title="Распределение по количеству изображений")
    fig_tables_count = px.bar(data["tables_count"], x="tables_count", y="count", title="Распределение по количеству таблиц")
    fig_title_density = px.bar(data["title_density"], x="Title_density", y="count", title="Распределение по количеству слов в заголовке")
    fig_keywords = px.bar(keyword_counts, x="keyword", y="count", title="Распределение по ключевым словам")
    
    # Данные для таблицы
    table_query = """
        SELECT font, images_count, tables_count, Design, Style, language, Slides_count, 
               Text_density, Keywords, Color_palette, Title_density, `PDF-name`
        FROM pdf_analysis LIMIT 10;
    """
    table_data = fetch_data(table_query)
    table = dbc.Table.from_dataframe(table_data, striped=True, bordered=True, hover=True)
    data_quality_metrics = calculate_data_quality_metrics(data)
    table_metrics = dbc.Table.from_dataframe(data_quality_metrics, striped=True, bordered=True, hover=True)

    
    # Ensure figures are valid
    return (fig_design, fig_font, fig_images_count, fig_tables_count, fig_title_density, fig_keywords, table, table_metrics)



# Запуск Dash приложения
if __name__ == "__main__":
    app.run_server(debug=True)
