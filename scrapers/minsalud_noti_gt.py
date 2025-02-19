import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import json

async def scrape_mspas_noticias():
    print("[MSPAS Noticias_GT] Iniciando scraping...")
    base_url = "https://www.mspas.gob.gt"
    url = f"{base_url}/noticias-mspas"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            print(f"[MSPAS Noticias_GT] Accediendo a URL: {url}")
            await page.goto(url, timeout=60000)
            
            # Esperar a que cargue el contenido
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_selector("article.itemView", timeout=20000)

            # Extraer HTML y analizarlo con BeautifulSoup
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Obtener todas las noticias
            noticias = soup.select("article.itemView")
            if not noticias:
                print("[MSPAS Noticias_GT] ⚠️ No se encontraron noticias.")
                return []

            items = []

            for noticia in noticias:
                try:
                    # Extraer título y URL
                    link = noticia.select_one("h2.uk-article-title a")
                    if not link:
                        continue
                    
                    title = link.text.strip()
                    noticia_url = link["href"]
                    noticia_url = f"{base_url}{noticia_url}" if noticia_url.startswith("/") else noticia_url

                    # Extraer fecha
                    fecha_element = noticia.select_one("span.itemDateCreated")
                    fecha = _parse_date(fecha_element.text.strip()) if fecha_element else datetime.now().date()

                    # Extraer descripción
                    descripcion_element = noticia.select_one("div.itemIntroText p")
                    descripcion = descripcion_element.text.strip() if descripcion_element else title

                    # Extraer imagen
                    img_element = noticia.select_one("div.itemImageBlock img")
                    imagen_url = img_element["src"] if img_element else None
                    if imagen_url and not imagen_url.startswith("http"):
                        imagen_url = f"{base_url}{imagen_url}"

                    # Extraer categoría
                    categoria_element = noticia.select_one("span.itemCategory a")
                    categoria = categoria_element.text.strip() if categoria_element else "Noticias"

                    # Crear objeto de noticia
                    item = {
                        "title": title,
                        "description": descripcion,
                        "source_url": noticia_url,
                        "source_type": "mspas_noticias_gt",
                        "country": "Guatemala",
                        "presentation_date": fecha,
                        "category": categoria,
                        "institution": "Ministerio de Salud Guatemala",
                        "metadata": json.dumps({"imagen": imagen_url})
                    }

                    items.append(item)
                    print(f"[MSPAS Noticias_GT] ✅ Noticia procesada: {title[:100]}")

                except Exception as e:
                    print(f"[MSPAS Noticias_GT] ⚠️ Error procesando noticia: {str(e)}")
                    continue

            print(f"[MSPAS Noticias_GT] 🎯 Se encontraron {len(items)} noticias")
            return items

        except Exception as e:
            print(f"[MSPAS Noticias_GT] ❌ Error: {str(e)}")
            return []
        finally:
            await browser.close()


def _parse_date(fecha_str):
    """
    Convierte fechas en español como "28 Enero 2025." a formato datetime.
    Si falla, usa la fecha actual.
    """
    meses = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }

    try:
        fecha_str = fecha_str.replace(".", "").strip()  # Eliminar punto final
        dia, mes, anio = fecha_str.split()
        mes_num = meses[mes.lower()]
        return datetime(int(anio), mes_num, int(dia)).date()
    except Exception as e:
        print(f"[MSPAS Noticias_GT] ⚠️ Error procesando fecha '{fecha_str}', se usará la fecha actual: {e}")
        return datetime.now().date()


if __name__ == "__main__":
    # Ejecutar el scraper y mostrar los resultados en JSON
    noticias = asyncio.run(scrape_mspas_noticias())
    print(json.dumps([{
        **noticia,
        'presentation_date': noticia['presentation_date'].strftime('%Y-%m-%d') if noticia['presentation_date'] else None
    } for noticia in noticias], indent=4, ensure_ascii=False))
