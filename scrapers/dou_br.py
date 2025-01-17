import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from datetime import datetime
import json

async def scrape_in_jornal_minsaude():
    """
    Scraper para la página del Diário Oficial da União (Ministério da Saúde) con Crawl4AI.
    """
    base_url = "https://www.in.gov.br"
    search_url = f"{base_url}/leiturajornal?org=Minist%C3%A9rio%20da%20Sa%C3%BAde"

    # Configurar el navegador
    browser_config = BrowserConfig(
        headless=True,  # Cambiar a False si necesitas depurar
        viewport_width=1280,
        viewport_height=720,
        java_script_enabled=True,  # Habilitar JavaScript
        verbose=True
    )

    # Configurar la ejecución del crawler
    async def configure_run_config():
        return CrawlerRunConfig(
            wait_for="css:ul.ul-materias > li.materia-link",  # Espera hasta que las noticias estén disponibles
            scroll_delay=0.5,  # Si la página usa scroll dinámico, agrega un pequeño retraso
            scan_full_page=True  # Scrollea la página para cargar todo el contenido dinámico
        )

    async def process_page(html):
        """
        Procesa el contenido HTML y extrae las noticias.
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        items = []

        noticias = soup.select("ul.ul-materias > li.materia-link")
        if not noticias:
            print("No se encontraron noticias en esta página.")
            return items

        for noticia in noticias:
            try:
                # Extraer título y enlace
                title_tag = noticia.select_one("h5.title-marker a")
                title = title_tag.text.strip() if title_tag else "Sin título"
                link = title_tag["href"] if title_tag else None
                full_url = f"{base_url}{link}" if link and not link.startswith("http") else link

                # Extraer sección, órgano y fecha de publicación
                breadcrumb = noticia.select_one("ol.breadcrumb")
                section = breadcrumb.select_one(".secao-marker").text.strip() if breadcrumb else "Sin sección"
                org = breadcrumb.select_one(".hierarchy-item-marker").text.strip() if breadcrumb else "Sin órgano"
                pub_info = breadcrumb.select_one(".publication-info-marker").text.strip() if breadcrumb else "Sin información"

                # Extraer descripción
                description = noticia.select_one("p.abstract-marker").text.strip() if noticia.select_one("p.abstract-marker") else "Sin descripción"

                # Crear el diccionario del item
                item = {
                    'title': title,
                    'description': description,
                    'source_url': full_url,
                    'source_type': "Diário Oficial da União",
                    'category': "Normas",
                    'country': "Brasil",
                    'institution': "Ministério da Saúde",
                    'metadata': {
                        'section': section,
                        'organization': org,
                        'publication_info': pub_info
                    }
                }
                items.append(item)
            except Exception as e:
                print(f"Error procesando noticia: {e}")
        return items

    async with AsyncWebCrawler(config=browser_config) as crawler:
        all_items = []
        next_page = search_url
        page_number = 1

        while next_page:
            print(f"Procesando página {page_number}: {next_page}")
            config = await configure_run_config()
            result = await crawler.arun(next_page, config=config)

            if not result.success:
                print(f"Error procesando la página: {result.error_message}")
                break

            # Procesar el HTML obtenido
            page_items = await process_page(result.cleaned_html)
            all_items.extend(page_items)

            # Verificar si existe un enlace a la siguiente página
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(result.cleaned_html, "html.parser")
            next_button = soup.select_one(".pagination .pagination-button:-soup-contains('Próximo »')")
            next_page = f"{base_url}{next_button['href']}" if next_button and next_button.has_attr("href") else None
            page_number += 1

        return all_items


if __name__ == "__main__":
    items = asyncio.run(scrape_in_jornal_minsaude())

    # Formatear salida como JSON
    print(json.dumps(items, indent=4, ensure_ascii=False))
