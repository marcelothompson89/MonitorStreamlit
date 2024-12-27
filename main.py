# main.py
import asyncio
from sqlalchemy.exc import IntegrityError

# Scrapers
from scrapers.anamed_cl import scrape_anamed
from scrapers.congreso_comu_pe import scrape_congreso
from scrapers.digemid_pe import scrape_digemid_noticias
from scrapers.digesa_comu_pe import scrape_digesa_comunicaciones
from scrapers.digesa_noticias_pe import scrape_digesa_noticias
from scrapers.diputados_noti_cl import scrape_diputados_noticias
from scrapers.diputados_proyectos_cl import scrape_diputados_proyectos
from scrapers.congreso_proyectos_pe import scrape_congreso_proyectos
from scrapers.ispch_noticias_cl import scrape_ispch_noticias
from scrapers.ispch_resoluciones_cl import scrape_ispch_resoluciones
from scrapers.minsa_normas_pe import scrape_minsa_normas
from scrapers.minsa_noticias_pe import scrape_minsa_noticias
from scrapers.senado_noticias_cl import scrape_senado_noticias

# DB
from database.db import SessionLocal, engine
from database.models import Base, Alerta

async def run_scrapers():
    # Crea las tablas si no existen
    Base.metadata.create_all(bind=engine)

    # Usamos el contexto síncrono normal
    session = SessionLocal()
    
    def save_items(items, source_name):
        saved_count = 0
        duplicate_count = 0
        
        for item in items:
            # Extraer los valores de metadata si es un diccionario
            metadata = item.get("metadata", {})
            if isinstance(metadata, dict):
                metadata_nota_url = metadata.get("nota_url")
                metadata_publicacion_url = metadata.get("publicacion_url")
            else:
                metadata_nota_url = metadata
                metadata_publicacion_url = None

            alerta = Alerta(
                title=item.get("title"),
                description=item.get("description"),
                source_type=item.get("source_type"),
                category=item.get("category"),
                country=item.get("country"),
                source_url=item.get("source_url"),
                institution=item.get("institution"),
                presentation_date=item.get("presentation_date"),
                metadata_nota_url=metadata_nota_url,
                metadata_publicacion_url=metadata_publicacion_url
            )
            try:
                session.add(alerta)
                session.commit()
                saved_count += 1
            except IntegrityError:
                session.rollback()
                duplicate_count += 1
                continue
            
        print(f"[{source_name}] Se encontraron {len(items)} noticias")
        if duplicate_count > 0:
            print(f"[{source_name}] {duplicate_count} noticias duplicadas ignoradas")
        if saved_count > 0:
            print(f"[{source_name}] {saved_count} noticias nuevas guardadas")
    
    try:
        # 1. ANAMED
        anamed_items = await scrape_anamed()
        save_items(anamed_items, "ANAMED_CL")

        # 2. CONGRESO
        congreso_items = await scrape_congreso()
        save_items(congreso_items, "CONGRESO_PE")

        # 3. DIGEMID
        digemid_items = await scrape_digemid_noticias()
        save_items(digemid_items, "DIGEMID_PE")

        # 4. DIGESA COMUNICACIONES
        digesa_comu_items = await scrape_digesa_comunicaciones()
        save_items(digesa_comu_items, "DIGESA Comunicaciones_PE")

        # 5. DIGESA NOTICIAS
        digesa_noti_items = await scrape_digesa_noticias()
        save_items(digesa_noti_items, "DIGESA Noticias_PE")

        # 6. DIPUTADOS CHILE NOTICIAS
        diputados_items = await scrape_diputados_noticias()
        save_items(diputados_items, "Diputados Noticias_CL")

        # 7. DIPUTADOS CHILE PROYECTOS
        diputados_proyectos_items = await scrape_diputados_proyectos()
        save_items(diputados_proyectos_items, "Diputados Proyectos_CL")

        # 8. CONGRESO PERU PROYECTOS
        congreso_proyectos_items = await scrape_congreso_proyectos()
        save_items(congreso_proyectos_items, "CONGRESO Proyectos_PE")

        # 9. ISPCH CHILE NOTICIAS
        ispch_noticias_items = await scrape_ispch_noticias()
        save_items(ispch_noticias_items, "ISPCH Noticias_CL")

        # 10. ISPCH CHILE RESOLUCIONES
        ispch_resoluciones_items = await scrape_ispch_resoluciones()
        save_items(ispch_resoluciones_items, "ISPCH Resoluciones_CL")

        # 11. MINSA PERU NORMAS
        minsa_normas_items = await scrape_minsa_normas()
        save_items(minsa_normas_items, "MINSA Normas_PE")

        # 12. MINSA PERU NOTICIAS
        minsa_noticias_items = await scrape_minsa_noticias()
        save_items(minsa_noticias_items, "MINSA Noticias_PE")

        # 13. SENADO PERU NOTICIAS
        senado_noticias_items = await scrape_senado_noticias()
        save_items(senado_noticias_items, "Senado Noticias_CL")

    except Exception as e:
        print(f"Error en run_scrapers: {str(e)}")
        raise e
    finally:
        session.close()

def main():
    asyncio.run(run_scrapers())

if __name__ == "__main__":
    main()
