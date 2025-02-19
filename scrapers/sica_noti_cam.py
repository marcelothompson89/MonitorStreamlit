import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def scrape_sica_cam():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://www.sica.int/consulta/noticias_401_3_1.html"
        print(f"[SICA Noticias] Accediendo a: {url}")
        await page.goto(url, timeout=60000)

        # Esperar que las noticias estén cargadas
        await page.wait_for_selector("tbody tr.k-master-row", timeout=10000)

        # Obtener todas las filas de noticias
        noticias = await page.query_selector_all("tbody tr.k-master-row")

        items = []

        for noticia in noticias:
            try:
                # Extraer título y URL
                title_element = await noticia.query_selector("h4 a")
                title = await title_element.inner_text() if title_element else "Sin título"
                news_url = await title_element.get_attribute("href") if title_element else "#"
                news_url = f"https://www.sica.int{news_url}" if news_url.startswith("/") else news_url

                # Extraer fecha desde el atributo datetime
                date_element = await noticia.query_selector("h5 time")
                fecha_iso = await date_element.get_attribute("datetime") if date_element else None
                fecha = _convert_date_iso(fecha_iso) if fecha_iso else None

                # Extraer descripción completa
                description_element = await noticia.query_selector("td span")
                description = await description_element.inner_text() if description_element else "Sin descripción"

                # Extraer fuente (quitar el texto 'Publicado por :')
                institution_element = await noticia.query_selector("h5")
                institution = await institution_element.inner_text() if institution_element else "SICA"
                institution = institution.split(":")[-1].strip()  # Quitar 'Publicado por :'

                # Crear objeto de noticia
                item = {
                    "title": title,
                    "description": title,
                    "source_url": news_url,
                    "source_type": "sica_noticias",
                    "country": "Centroamérica",
                    "presentation_date": fecha,
                    "category": "Noticias",
                    "institution": institution,
                    "metadata": json.dumps({"tipo": "Noticia"})
                }

                items.append(item)
                print(f"[SICA Noticias] ✅ Noticia extraída: {title[:100]}")

            except Exception as e:
                print(f"[SICA Noticias] ⚠️ Error procesando noticia: {str(e)}")
                continue

        await browser.close()

        print(f"[SICA Noticias] 🎯 Se encontraron {len(items)} noticias")
        return items

def _convert_date_iso(fecha_iso):
    """
    Convierte una fecha con formato largo (ejemplo: 'Mon Feb 17 2025 21:03:00 GMT-0300 (hora estándar de Argentina)')
    a formato 'YYYY-MM-DD', eliminando la hora y zona horaria.
    """
    try:
        fecha_limpia = fecha_iso.split(" ")[1:4]  # Extraer solo "Feb 17 2025"
        fecha_str = " ".join(fecha_limpia)  # Convertir a string "Feb 17 2025"
        fecha_obj = datetime.strptime(fecha_str, "%b %d %Y")  # Convertir a objeto datetime
        return fecha_obj.date()  # Retornar solo la fecha
    except Exception as e:
        print(f"[SICA Noticias] ⚠️ Error convirtiendo fecha '{fecha_iso}': {e}")
    return None

# if __name__ == "__main__":
#     # Ejecutar el scraper y mostrar los resultados en JSON
#     noticias = asyncio.run(scrape_sica())
#     print(json.dumps([{
#         **noticia,
#         'presentation_date': noticia['presentation_date'].strftime('%Y-%m-%d') if noticia['presentation_date'] else None
#     } for noticia in noticias], indent=4, ensure_ascii=False))
