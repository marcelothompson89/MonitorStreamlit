import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async def scrape_normas_legales():
    """
    Scraper para extraer normas legales de https://normas.leg.br/busca
    usando Crawl4AI.
    """
    url = "https://normas.leg.br/busca?q=&anoInicial=1889&anoFinal=2025&pagina=0&pageSize=10"

    # Configuración del navegador
    browser_config = BrowserConfig(
        headless=True,  # Ejecuta el navegador en modo headless
        viewport_width=1280,
        viewport_height=720,
        verbose=True
    )

    # Configuración del crawler
    run_config = CrawlerRunConfig(
        css_selector="table.mat-table tbody tr",  # Selector CSS para filas de la tabla
        word_count_threshold=0,  # No ignorar contenido por longitud
        wait_for="css:table.mat-table",  # Esperar a que la tabla se cargue
        cache_mode="BYPASS"  # Siempre obtener contenido actualizado
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            # Ejecutar el crawler
            result = await crawler.arun(url=url, config=run_config)

            if not result.success:
                print(f"Error en la extracción: {result.error_message}")
                return []

            # Procesar el contenido limpio devuelto por Crawl4AI
            cleaned_html = result.cleaned_html
            if not cleaned_html:
                print("No se encontró contenido.")
                return []

            # Extraer datos de las filas usando BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(cleaned_html, "html.parser")
            rows = soup.select("table.mat-table tbody tr")

            items = []
            for row in rows:
                try:
                    # Extraer norma
                    norma = row.select_one("td.mat-column-nome a").get_text(strip=True)
                    # Extraer ementa
                    ementa = row.select_one("td.mat-column-ementa .ementa").get_text(strip=True)
                    # Extraer origen
                    origen = row.select_one("td.mat-column-ementa .nome-processo").get_text(strip=True)

                    # Crear objeto
                    item = {
                        "norma": norma,
                        "ementa": ementa,
                        "origen": origen,
                        "source_url": url
                    }
                    items.append(item)
                except Exception as e:
                    print(f"Error procesando fila: {e}")

            return items

        except Exception as e:
            print(f"Error general: {e}")
            return []


if __name__ == "__main__":
    # Ejecutar el scraper y mostrar resultados
    items = asyncio.run(scrape_normas_legales())
    print
