import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import json


async def scrape_cepal_noticias():
    """
    Scraper para el sitio de noticias de CEPAL utilizando Playwright.
    """
    base_url = "https://www.cepal.org"
    url = "https://www.cepal.org/es/news/list/language/es"
    items = []  # Lista para almacenar las noticias
    fecha_actual = datetime.now().date()  # Fecha del día actual

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Navegar a la página
            await page.goto(url)
            # Esperar a que se carguen las noticias dinámicas
            await page.wait_for_selector(".views-row", timeout=10000)

            # Obtener el contenido HTML de la página
            html_content = await page.content()
            soup = BeautifulSoup(html_content, "html.parser")

            # Buscar las noticias
            noticias = soup.select("div.views-row")
            print(f"Noticias encontradas: {len(noticias)}")

            for noticia in noticias:
                try:
                    # A) Fecha de la noticia
                    fecha_tag = noticia.select_one("span.date-display-single")
                    fecha_texto = fecha_tag.text.strip() if fecha_tag else None
                    fecha_hora = _parse_date_from_text(fecha_texto) if fecha_texto else fecha_actual

                    # B) Título y enlace
                    titulo_tag = noticia.select_one("div.views-field-title-field a")
                    titulo_texto = titulo_tag.text.strip() if titulo_tag else "SIN TÍTULO"
                    enlace_relativo = titulo_tag["href"] if titulo_tag else None
                    enlace_url = f"{base_url}{enlace_relativo}" if enlace_relativo else None

                    # C) Tipo de noticia
                    tipo_tag = noticia.select_one("span.views-field-type")
                    tipo_texto = tipo_tag.text.strip() if tipo_tag else "No especificado"

                    # D) Descripción
                    descripcion_tag = noticia.select_one("div.views-field-field-teaser span.field-content")
                    descripcion = descripcion_tag.text.strip() if descripcion_tag else "Sin descripción disponible"

                    # E) Imagen
                    img_tag = noticia.select_one("div.views-field-field-news-image img")
                    imagen_url = img_tag["src"] if img_tag else None

                    # Crear el diccionario del item
                    item = {
                        "title": titulo_texto,
                        "description": f"{descripcion}\nTipo: {tipo_texto}\nImagen: {imagen_url}" if imagen_url else descripcion,
                        "source_type": "CEPAL",
                        "category": "Noticias",
                        "country": "Regional",
                        "source_url": enlace_url,
                        "institution": "CEPAL",
                        "presentation_date": fecha_hora,
                    }
                    items.append(item)

                except Exception as e:
                    print(f"Error procesando noticia: {e}")

        except Exception as e:
            print(f"Error al procesar la página: {e}")

        finally:
            await browser.close()

    # Imprimir resultados
    print(f"Noticias procesadas: {len(items)}")
    return items


def _parse_date_from_text(text):
    """
    Intenta extraer una fecha de un texto como "3 de enero de 2025".
    """
    from locale import setlocale, LC_TIME
    import re

    try:
        setlocale(LC_TIME, "es_ES.UTF-8")  # Cambiar al idioma español para manejar fechas
    except:
        print("Advertencia: El sistema no tiene configurado el locale para 'es_ES.UTF-8'.")

    try:
        return datetime.strptime(text, "%d de %B de %Y").date()
    except ValueError:
        print(f"No se pudo parsear la fecha: {text}")
        return None


# if __name__ == "__main__":
#     # Ejecutar el scraper
#     items = asyncio.run(scrape_cepal_noticias())

#     # Mostrar resultados en formato JSON
#     print(json.dumps([{
#         **item,
#         'presentation_date': item['presentation_date'].strftime('%Y-%m-%d') if item['presentation_date'] else None
#     } for item in items], indent=4, ensure_ascii=False))
