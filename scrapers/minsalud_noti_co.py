from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import asyncio
from datetime import datetime, date


async def scrape_minsalud_news():
    """
    Scraper para las noticias del Ministerio de Salud utilizando Playwright.
    """
    base_url = "https://www.minsalud.gov.co"
    url = "https://www.minsalud.gov.co/CC/Paginas/noticias-2024.aspx"
    items = []

    async with async_playwright() as p:
        # Lanzar navegador en modo headless
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        # Esperar a que el contenedor de noticias se cargue
        await page.wait_for_selector("#cbqwpctl00_ctl53_g_0e2217c2_285e_469e_a426_7d7dc98da0a4")

        # Extraer el contenido HTML renderizado
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Buscar noticias dentro del div con el ID relevante
        noticias_div = soup.find("div", id="cbqwpctl00_ctl53_g_0e2217c2_285e_469e_a426_7d7dc98da0a4")
        noticias = noticias_div.find_all("div", class_="link-item") if noticias_div else []

        for noticia in noticias:
            try:
                # A) Extraer título y enlace
                titulo_a = noticia.find("a")
                title = titulo_a.get_text(strip=True) if titulo_a else "SIN TÍTULO"
                enlace_relativo = titulo_a["href"] if titulo_a else None
                source_url = f"{base_url}{enlace_relativo}" if enlace_relativo else None

                # B) Extraer descripción
                fecha_div = noticia.find("div", class_="description")
                description = fecha_div.get_text(strip=True) if fecha_div else ""

                # C) Extraer fecha
                fecha_texto = description  # La fecha está dentro de la descripción
                presentation_date = _parse_date(fecha_texto)

                # Si no se encuentra una fecha válida, usar la fecha actual
                if not presentation_date:
                    presentation_date = date.today()

                # Crear objeto en el formato esperado
                item = {
                    'title': title,
                    'description': description,
                    'source_url': source_url,
                    'source_type': "Ministerio de Salud Noticias",
                    'category': "Noticias",
                    'country': "Colombia",
                    'institution': "Ministerio de Salud y Protección Social",
                    'presentation_date': presentation_date,
                }

                items.append(item)
            except Exception as e:
                print(f"Error procesando noticia: {e}")

        await browser.close()

    return items


def _parse_date(date_str):
    """
    Parsear una fecha en formato conocido como "06/01/2025" o similar.
    """
    if not date_str:
        return None
    try:
        # Intentar parsear con formato dd/mm/yyyy
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        return None


if __name__ == "__main__":
    # Ejecutar el scraper de forma asíncrona
    items = asyncio.run(scrape_minsalud_news())

    # Imprimir resultados
    for item in items:
        print(item)
