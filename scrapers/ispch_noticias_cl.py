import asyncio
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import json

async def scrape_ispch_noticias():
    print("[ISPCH Noticias_CL] Iniciando scraping...")
    url = "https://www.ispch.gob.cl/noticia/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            print(f"[ISPCH Noticias_CL] Accediendo a URL: {url}")
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            print(f"[ISPCH Noticias_CL] Respuesta recibida. Status code: {response.status_code}")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontrar todas las noticias
            noticias = soup.find_all('div', class_='')
            items = []
            
            for noticia in noticias:
                try:
                    # Extraer título y URL
                    link = noticia.find('a', class_='link-search')
                    if not link:
                        continue
                        
                    title = link.find('h4').text.strip()
                    url = link['href']
                    
                    # Extraer fecha
                    fecha_element = link.find('div', class_='small').find('time')
                    if not fecha_element:
                        continue
                        
                    fecha_str = fecha_element.text.strip()  # "19 diciembre, 2024"
                    # Convertir mes a número
                    meses = {
                        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
                        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                    }
                    try:
                        dia, mes, anio = fecha_str.replace(',', '').split()
                        mes_num = meses[mes.lower()]
                        fecha = datetime(int(anio), mes_num, int(dia))
                    except (ValueError, KeyError):
                        print(f"[ISPCH Noticias_CL] Error procesando fecha: {fecha_str}")
                        continue
                    
                    # Extraer descripción
                    description = link.find('p').text.strip()
                    if not description:
                        description = title
                    
                    # Crear el objeto de la noticia
                    item = {
                        "title": title,
                        "description": description,
                        "source_url": url,
                        "source_type": "ispch_noticias_cl",
                        "country": "Chile",
                        "presentation_date": fecha,
                        "institution": "ispch_noticias_cl",
                        "metadata": json.dumps({
                            "tipo": "Noticia ISPCH"
                        })
                    }
                    
                    items.append(item)
                    print(f"[ISPCH Noticias_CL] Noticia procesada: {title[:100]}")
                    
                except Exception as e:
                    print(f"[ISPCH Noticias_CL] Error procesando noticia: {str(e)}")
                    continue
            
            print(f"[ISPCH Noticias_CL] Se encontraron {len(items)} noticias")
            return items
            
        except Exception as e:
            print(f"[ISPCH Noticias_CL] Error: {str(e)}")
            return []
