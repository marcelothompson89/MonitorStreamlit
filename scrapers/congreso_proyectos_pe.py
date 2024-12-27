import asyncio
from datetime import datetime
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

async def scrape_congreso_proyectos():
    print("[Congreso Proyectos_PE] Iniciando scraping...")
    
    # Configurar opciones de Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Configurar el servicio de Chrome
    service = Service("/usr/local/bin/chromedriver")
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        
        url = "https://wb2server.congreso.gob.pe/spley-portal/#/expediente/search"
        print(f"[Congreso Proyectos_PE] Accediendo a URL: {url}")
        
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        
        # Esperar a que se cargue la tabla de manera más robusta
        print("[Congreso Proyectos_PE] Esperando que cargue la página...")
        time.sleep(10)  # Esperar a que cargue la SPA
        
        try:
            # Intentar múltiples selectores
            selectors = [
                "table.mat-table",
                "table",
                ".mat-table-container table",
                "[role='grid']"
            ]
            
            table = None
            for selector in selectors:
                try:
                    print(f"[Congreso Proyectos_PE] Intentando selector: {selector}")
                    table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if table:
                        print(f"[Congreso Proyectos_PE] Tabla encontrada con selector: {selector}")
                        break
                except:
                    continue
            
            if not table:
                print("[Congreso Proyectos_PE] No se encontró la tabla principal")
                return []
            
            # Imprimir el HTML para debug
            print("[Congreso Proyectos_PE] HTML de la tabla:")
            print(table.get_attribute('outerHTML')[:500])
            
        except TimeoutException:
            print("[Congreso Proyectos_PE] Timeout esperando la tabla")
            return []
        
        # Esperar a que se carguen los datos
        time.sleep(5)
        
        # Buscar filas de proyectos con múltiples selectores
        rows = []
        row_selectors = [
            "tr.mat-row",
            "tr[role='row']",
            "tr.ng-star-inserted"
        ]
        
        for selector in row_selectors:
            rows = driver.find_elements(By.CSS_SELECTOR, selector)
            if rows:
                print(f"[Congreso Proyectos_PE] Encontradas {len(rows)} filas con selector {selector}")
                break
        
        if not rows:
            print("[Congreso Proyectos_PE] No se encontraron proyectos")
            return []
        
        items = []
        for row in rows:
            try:
                # Extraer datos básicos con múltiples intentos
                link = None
                link_selectors = [
                    "a.link-proyecto-acumulado",
                    "a[target='_blank']",
                    "a"
                ]
                
                for selector in link_selectors:
                    try:
                        link = row.find_element(By.CSS_SELECTOR, selector)
                        if link:
                            break
                    except:
                        continue
                
                if not link:
                    print("[Congreso Proyectos_PE] No se encontró el link del proyecto")
                    continue
                
                numero = link.text.strip()
                href = link.get_attribute("href")
                
                # Extraer otros campos
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 6:
                    print(f"[Congreso Proyectos_PE] Fila no tiene suficientes columnas: {len(cells)}")
                    continue
                
                fecha_str = cells[1].text.strip()
                titulo = cells[2].find_element(By.CSS_SELECTOR, "span.ellipsis").text.strip()
                estado = cells[3].text.strip()
                proponente = cells[4].text.strip()
                
                # Extraer autores
                autores = []
                try:
                    autores_ul = cells[5].find_element(By.TAG_NAME, "ul")
                    autores_li = autores_ul.find_elements(By.TAG_NAME, "li")
                    for autor_li in autores_li:
                        autor_text = autor_li.text.replace("ver más...", "").strip()
                        if autor_text:
                            autores.append(autor_text)
                except:
                    print(f"[Congreso Proyectos_PE] No se pudieron extraer autores para proyecto {numero}")
                
                # Convertir fecha
                try:
                    fecha = datetime.strptime(fecha_str, '%d/%m/%Y')
                except ValueError:
                    print(f"[Congreso Proyectos_PE] Error procesando fecha: {fecha_str}")
                    fecha = datetime.now()
                
                # Construir descripción con autores
                autores_str = ", ".join(autores[:3])
                if len(autores) > 3:
                    autores_str += f" y {len(autores)-3} más"
                
                item = {
                    "title": titulo,
                    "description": f"Proyecto de Ley N° {numero} - Estado: {estado} - Proponente: {proponente}\nAutores: {autores_str}",
                    "source_url": href,
                    "source_type": "congreso_proyectos_pe",
                    "country": "Perú",
                    "presentation_date": fecha,
                    "institution": "congreso_proyectos_pe",
                    "metadata": json.dumps({
                        "numero_expediente": numero,
                        "estado": estado,
                        "proponente": proponente,
                        "autores": autores,
                        "periodo": "2021-2026"
                    })
                }
                items.append(item)
                print(f"[Congreso Proyectos_PE] Proyecto procesado: {numero}")
                
            except Exception as e:
                print(f"[Congreso Proyectos_PE] Error procesando proyecto: {str(e)}")
                continue
        
        print(f"[Congreso Proyectos_PE] Se encontraron {len(items)} proyectos")
        return items
        
    except Exception as e:
        print(f"[Congreso Proyectos_PE] Error: {str(e)}")
        return []
        
    finally:
        try:
            driver.quit()
            print("[Congreso Proyectos_PE] Navegador cerrado")
        except:
            pass
