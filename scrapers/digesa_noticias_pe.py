import asyncio
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import aiohttp
from urllib.parse import urljoin
import json

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Setiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

async def get_month_news(soup, month_number, year):
    month_name = MESES[month_number]
    header = soup.find('h4', string=re.compile(f"{month_name}.*{year}", re.IGNORECASE))
    if not header:
        return []
    
    items = []
    current_list = header.find_next('ul')
    if current_list:
        for link in current_list.find_all('a'):
            href = link.get('href')
            texto = link.text.strip()
            fecha_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', texto)
            
            if fecha_match:
                dia, mes, anio = fecha_match.groups()
                fecha = datetime.strptime(f"{anio}-{mes}-{dia}", "%Y-%m-%d")
                noticia_url = urljoin("http://www.digesa.minsa.gob.pe/noticias/index.asp", href)
                
                # Quitar la fecha del inicio del texto, si corresponde
                titulo = re.sub(r'^\d{2}\.\d{2}\.\d{4}\.\s*', '', texto).strip()
                
                metadata = {
                    'tipo': 'noticia',
                    'año': str(year),
                    'fecha': fecha.strftime("%Y-%m-%d"),
                    'titulo': titulo,
                    'url': noticia_url
                }
                item = {
                    'title': titulo,
                    'description': titulo,
                    'country': 'Perú',
                    'source_url': noticia_url,
                    'source_type': 'DIGESA',
                    'presentation_date': fecha,
                    'institution': 'DIGESA_noticias_pe',
                    'metadata': json.dumps(metadata)
                }
                items.append(item)
    
    return items

async def scrape_digesa_noticias():
    print("[DIGESA Noticias Scraper] Iniciando scraping...")
    base_url = "http://www.digesa.minsa.gob.pe/noticias/index.asp"
    items = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    current_date = datetime.now()
                    current_month = current_date.month
                    current_year = current_date.year
                    
                    # Mes actual
                    items = await get_month_news(soup, current_month, current_year)
                    
                    # Si no hay nada en el mes actual, intentamos el mes anterior
                    if not items:
                        if current_month == 1:
                            previous_month = 12
                            previous_year = current_year - 1
                        else:
                            previous_month = current_month - 1
                            previous_year = current_year
                        
                        items = await get_month_news(soup, previous_month, previous_year)
                    
                    print(f"[DIGESA Noticias_PE] Se encontraron {len(items)} noticias")
                    return items
                else:
                    print(f"[DIGESA Noticias_PE] Error HTTP: {response.status}")
                    return []
    except Exception as e:
        print(f"[DIGESA Noticias_PE] Error: {str(e)}")
        return []
