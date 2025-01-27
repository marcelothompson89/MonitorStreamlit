import asyncio
from playwright.async_api import async_playwright


async def scrape_minsalud_decre2025():
    url = "https://www.minsalud.gov.co/Paginas/Norm_Decretos.aspx"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        # Guardar el HTML inicial para depuración
        html_content = await page.content()
        with open("debug_initial_minsalud.html", "w", encoding="utf-8") as file:
            file.write(html_content)

        try:
            # Selector para los botones expandir
            expand_button_selector = "tr.ms-gb img[alt='expandir']"

            # Buscar todos los botones expandir
            expand_buttons = await page.query_selector_all(expand_button_selector)
            if not expand_buttons:
                print("No se encontraron botones con el atributo alt='expandir'.")
                return

            print(f"Se encontraron {len(expand_buttons)} botones expandir. Verificando el correcto...")

            expand_button = None

            for button in expand_buttons:
                parent_row = await button.evaluate_handle('el => el.closest("tr")')
                if parent_row:
                    text = await parent_row.inner_text()
                    print(f"Texto de la fila encontrada: {text.strip()}")
                    if "2025" in text:
                        expand_button = button
                        break

            if expand_button:
                print("Haciendo clic para expandir el año 2025...")
                await expand_button.click()
                await page.wait_for_timeout(3000)  # Esperar después del clic

                # Guardar el DOM después del clic
                html_content = await page.content()
                with open("debug_after_click_minsalud.html", "w", encoding="utf-8") as file:
                    file.write(html_content)
            else:
                print("Botón para expandir el año 2025 no encontrado.")
                return

            # Intentar capturar el tbody relacionado al año 2025
            tbody_selector_pattern = "tbody[id^='tbod'][isloaded='true']"
            tbody_elements = await page.query_selector_all(tbody_selector_pattern)
            print(f"Se encontraron {len(tbody_elements)} elementos tbody con isloaded='true'.")

            tbody_2025 = None

            for tbody in tbody_elements:
                rows = await tbody.query_selector_all("tr")
                if rows:
                    first_row_text = await rows[0].inner_text()
                    print(f"Texto de la primera fila del tbody: {first_row_text.strip()}")
                    if "2025" in first_row_text:
                        tbody_2025 = tbody
                        break

            if not tbody_2025:
                print("No se encontró el tbody relacionado al año 2025.")
                html_content = await page.content()
                with open("debug_minsalud_error.html", "w", encoding="utf-8") as file:
                    file.write(html_content)
                print("Archivo guardado como debug_minsalud_error.html para inspección.")
                return

            # Extraer los datos del tbody
            print("Extrayendo los datos del tbody...")
            rows = await tbody_2025.query_selector_all("tr")
            results = []

            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 6:
                    year = await cells[1].inner_text()
                    title = await cells[2].inner_text()
                    link = await cells[2].query_selector("a")
                    url = await link.get_attribute("href") if link else None
                    description = await cells[3].inner_text()
                    category = await cells[4].inner_text()
                    created = await cells[5].inner_text()

                    results.append({
                        "Año": year.strip(),
                        "Título": title.strip(),
                        "Enlace": f"https://www.minsalud.gov.co{url.strip()}" if url else None,
                        "Descripción": description.strip(),
                        "Temática": category.strip(),
                        "Creado": created.strip()
                    })

            print("Resultados obtenidos:", results)

        except Exception as e:
            print(f"Error durante la extracción de los datos: {e}")

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_minsalud_decre2025())
