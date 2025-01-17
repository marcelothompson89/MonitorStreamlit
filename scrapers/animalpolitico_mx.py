from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import asyncio
from datetime import datetime, date


async def scrape_animal_politico_salud():
    """
    Scraper para la sección de salud de Animal Político utilizando Playwright.
    """
    base_url = "https://www.animalpolitico.com"
    url = "https://www.animalpolitico.com/salud/notas"
    items = []

    async with async_playwright() as p:
        # Lanzar navegador en modo headless
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        # Esperar a que los artículos se carguen
        await page.wait_for_selector(".grid .col-span-3")

        # Extraer el contenido HTML renderizado
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Buscar artículos dentro del contenedor principal
        contenedor = soup.find("div", class_="grid grid-cols-3 gap-4 mb-10")
        articulos = contenedor.find_all("div", class_="col-span-3") if contenedor else []

        for articulo in articulos:
            try:
                # A) Extraer título y enlace
                titulo_tag = articulo.find("a")
                title = titulo_tag.get_text(strip=True) if titulo_tag else "Sin título"
                enlace_relativo = titulo_tag["href"] if titulo_tag else None
                source_url = f"{base_url}{enlace_relativo}" if enlace_relativo else None

                # B) Extraer descripción
                descripcion_tag = articulo.find("div", class_="font-Inter-Bold")
                description = descripcion_tag.get_text(strip=True) if descripcion_tag else ""

                # C) Extraer fecha
                fecha_tag = articulo.find("div", class_="text-xs")
                fecha_texto = fecha_tag.get_text(strip=True) if fecha_tag else None
                presentation_date = _parse_date(fecha_texto)

                # Si no se encuentra una fecha válida, usar la fecha actual
                if not presentation_date:
                    presentation_date = date.today()

                # # D) Extraer imagen
                # img_tag = articulo.find("img")
                # imagen_url = img_tag["src"] if img_tag else None
                # description = f"{description}\nImagen: {imagen_url}" if imagen_url else description

                # Crear objeto en el formato esperado
                item = {
                    'title': description,
                    'description': description,
                    'source_url': source_url,
                    'source_type': "Animal Político periódico",
                    'category': "Noticias",
                    'country': "México",
                    'institution': "Animal Político",
                    'presentation_date': presentation_date,
                }

                items.append(item)
            except Exception as e:
                print(f"Error procesando artículo: {e}")

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


# if __name__ == "__main__":
#     # Ejecutar el scraper de forma asíncrona
#     items = asyncio.run(scrape_animal_politico_salud())

#     # Imprimir resultados
#     for item in items:
#         print(item)
