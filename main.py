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
from scrapers.anvisa_normas_br import scrape_anvisa
from scrapers.diputados_noti_br import scrape_camara_noticias_br
from scrapers.anvisa_noti_br import scrape_anvisa_noticias
from scrapers.senado_noti_br import scrape_senado_noticias_br
from scrapers.minsalud_noti_br import scrape_minsalud_noticias_br
from scrapers.dou_br import scrape_dou_br
from scrapers.congreso_normas_br import scrape_congreso_normas_br
from scrapers.minsalud_noti_mx import scrape_gob_mx_salud
from scrapers.minsalud_comu_mx import scrape_gob_mx_salud_comu
from scrapers.cofepris_noti_mx import scrape_cofepris_mx
from scrapers.animalpolitico_mx import scrape_animal_politico_salud
from scrapers.eluniversal_mx import scrape_el_universal_salud
from scrapers.periodico_proceso_mx import scrape_proceso_mx
from scrapers.boletinoficial_ar import scrape_boletin_oficial
from scrapers.anmat_noti_ar import scrape_anmat_noti_ar
from scrapers.minsalud_noti_ar import scrape_salud_noticias_ar
from scrapers.hcdn_ar import scrape_diputados_proyectos_ar
from scrapers.senado_noti_ar import scrape_senado_eventos
from scrapers.invima_noti_co import scrape_invima_noticias
from scrapers.congreso_legislativo_co import scrape_camara_proyectos_co


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

        # 14. ANVISA NORMAS BRASIL
        anvisa_normas_items = await scrape_anvisa()
        save_items(anvisa_normas_items, "ANVISA Normas_BR")

        # 15. ANVISA NOTICIAS BRASIL
        anvisa_noticias_items = await scrape_anvisa_noticias()
        save_items(anvisa_noticias_items, "ANVISA Noticias_BR")

        # 16. CAMARA BRASIL NOTICIAS
        camara_noticias_items = await scrape_camara_noticias_br()
        save_items(camara_noticias_items, "Diputados Noticias_BR")

        # 17. SENADO BRASIL NOTICIAS
        senado_noticias_items = await scrape_senado_noticias_br()
        save_items(senado_noticias_items, "Senado Noticias_BR")

        # 18. MINSA BRASIL NOTICIAS
        minsa_noticias_items = await scrape_minsalud_noticias_br()
        save_items(minsa_noticias_items, "MINSA Noticias_BR")

        # 19. DOU BRASIL NOTICIAS
        dou_noticias_items = await scrape_dou_br()
        save_items(dou_noticias_items, "DOU Normas_BR")

        # 20. CONGRESO BRASIL NORMAS
        congreso_normas_items = await scrape_congreso_normas_br()
        save_items(congreso_normas_items, "CONGRESO Normas_BR")

        # 21. GOB MX SALUD  
        gob_mx_salud_items = await scrape_gob_mx_salud()
        save_items(gob_mx_salud_items, "MINSA Noticias_MX")

        # 22. GOB MX SALUD COMUNICACIONES
        gob_mx_comunicaciones_items = await scrape_gob_mx_salud_comu()
        save_items(gob_mx_comunicaciones_items, "MINSA Comunicaciones_MX")

        # 23. COFEPRIS MX NOTICIAS
        cofepris_mx_items = await scrape_cofepris_mx()
        save_items(cofepris_mx_items, "COFEPRIS Noticias_MX")

        # 24. ANIMAL POLITICO SALUD
        animal_politico_salud_items = await scrape_animal_politico_salud()
        save_items(animal_politico_salud_items, "ANIMAL POLITICO SALUD_MX")

        # 25. EL UNIVERSAL SALUD
        el_universal_salud_items = await scrape_el_universal_salud()
        save_items(el_universal_salud_items, "EL UNIVERSAL SALUD_MX")

        # 26. PERIODICO PROCESO
        proceso_mx_items = await scrape_proceso_mx()
        save_items(proceso_mx_items, "PERIODICO PROCESO_MX")    

        # 27. BOLETIN OFICIAL ARGENTINA
        boletin_oficial_items = await scrape_boletin_oficial()
        save_items(boletin_oficial_items, "BOLETIN OFICIAL_AR")

        # 28. ANMAT NOTICIAS
        anmat_items = await scrape_anmat_noti_ar()
        save_items(anmat_items, "ANMAT Noticias_AR")

        # 29. MINSALUD NOTICIAS ARGENTINA
        minsalud_items = await scrape_salud_noticias_ar()
        save_items(minsalud_items, "MINSALUD Noticias_AR")

        # 30. DIPUTADOS PROYECTOS ARGENTINA
        diputados_proyectos_items = await scrape_diputados_proyectos_ar()
        save_items(diputados_proyectos_items, "DIPUTADOS PROYECTOS_AR")

        # 31. SENADO EVENTOS ARGENTINA
        senado_eventos_items = await scrape_senado_eventos()
        save_items(senado_eventos_items, "SENADO EVENTOS_AR")

        # 32. INVIMA NOTICIAS COLOMBIA
        invima_noticias_items = await scrape_invima_noticias()
        save_items(invima_noticias_items, "INVIMA Noticias_CO")

        # 33. CONGRESO LEGISLATIVO COLOMBIA
        camara_proyectos_items = await scrape_camara_proyectos_co()
        save_items(camara_proyectos_items, "CONGRESO LEGISLATIVO_CO")

    except Exception as e:
        print(f"Error en run_scrapers: {str(e)}")
        raise e
    finally:
        session.close()

def main():
    asyncio.run(run_scrapers())

if __name__ == "__main__":
    main()
