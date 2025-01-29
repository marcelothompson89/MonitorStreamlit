import asyncio
from sqlalchemy.exc import IntegrityError

# Importar los scrapers
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
from scrapers.minsalud_resol_co import scrape_minsalud_resoluciones
from scrapers.minsalud_decre_co import scrape_minsalud_decre
from scrapers.minsalud_noti_co import scrape_minsalud_news
from scrapers.paho_noti_reg import scrape_paho_noticias
from scrapers.parlatino_reg import scrape_parlatino
from scrapers.cepal_reg import scrape_cepal_noticias
from scrapers.wto_eping_glo import scrape_eping

# DB
from database.db import SessionLocal, engine
from database.models import Base, Alerta

async def run_scrapers():
    """Ejecuta los scrapers sin detener el proceso en caso de fallas."""
    
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    scrapers = [
        ("ANAMED_CL", scrape_anamed),
        ("CONGRESO_PE", scrape_congreso),
        ("DIGEMID_PE", scrape_digemid_noticias),
        ("DIGESA Comunicaciones_PE", scrape_digesa_comunicaciones),
        ("DIGESA Noticias_PE", scrape_digesa_noticias),
        ("Diputados Noticias_CL", scrape_diputados_noticias),
        ("Diputados Proyectos_CL", scrape_diputados_proyectos),
        ("CONGRESO Proyectos_PE", scrape_congreso_proyectos),
        ("ISPCH Noticias_CL", scrape_ispch_noticias),
        ("ISPCH Resoluciones_CL", scrape_ispch_resoluciones),
        ("MINSA Normas_PE", scrape_minsa_normas),
        ("MINSA Noticias_PE", scrape_minsa_noticias),
        ("Senado Noticias_CL", scrape_senado_noticias),
        ("ANVISA Normas_BR", scrape_anvisa),
        ("ANVISA Noticias_BR", scrape_anvisa_noticias),
        ("Diputados Noticias_BR", scrape_camara_noticias_br),
        ("Senado Noticias_BR", scrape_senado_noticias_br),
        ("MINSA Noticias_BR", scrape_minsalud_noticias_br),
        ("DOU Normas_BR", scrape_dou_br),
        ("CONGRESO Normas_BR", scrape_congreso_normas_br),
        ("MINSA Noticias_MX", scrape_gob_mx_salud),
        ("MINSA Comunicaciones_MX", scrape_gob_mx_salud_comu),
        ("COFEPRIS Noticias_MX", scrape_cofepris_mx),
        ("ANIMAL POLITICO SALUD_MX", scrape_animal_politico_salud),
        ("EL UNIVERSAL SALUD_MX", scrape_el_universal_salud),
        ("PERIODICO PROCESO_MX", scrape_proceso_mx),
        ("BOLETIN OFICIAL_AR", scrape_boletin_oficial),
        ("ANMAT Noticias_AR", scrape_anmat_noti_ar),
        ("MINSALUD Noticias_AR", scrape_salud_noticias_ar),
        ("DIPUTADOS PROYECTOS_AR", scrape_diputados_proyectos_ar),
        ("SENADO EVENTOS_AR", scrape_senado_eventos),
        ("INVIMA Noticias_CO", scrape_invima_noticias),
        ("CONGRESO LEGISLATIVO_CO", scrape_camara_proyectos_co),
        ("MINSALUD RESOLUCIONES_CO", scrape_minsalud_resoluciones),
        ("MINSALUD DECRETOS_CO", scrape_minsalud_decre),
        ("MINSALUD NOTICIAS_CO", scrape_minsalud_news),
        ("PAHO NOTICIAS_REG", scrape_paho_noticias),
        ("PARLATINO NOTICIAS_REG", scrape_parlatino),
        ("CEPAL NOTICIAS_REG", scrape_cepal_noticias),
        ("WTO EPING GLOBAL", scrape_eping),
    ]

    async def execute_scraper(name, scraper_function):
        try:
            print(f"[{name}] Ejecutando scraper...")
            items = await scraper_function()
            if items:
                save_items(items, name, session)
            print(f"[{name}] Finalizado correctamente ✅")
        except Exception as e:
            print(f"[{name}] ❌ Error en scraper: {str(e)}")

    async def execute_all_scrapers():
        """Ejecuta los scrapers de forma secuencial, pero maneja errores individualmente."""
        tasks = [execute_scraper(name, func) for name, func in scrapers]
        await asyncio.gather(*tasks)  # Ejecuta en paralelo para mayor eficiencia

    await execute_all_scrapers()
    session.close()

def save_items(items, source_name, session):
    """Guarda los ítems en la base de datos y maneja duplicados."""
    saved_count = 0
    duplicate_count = 0

    for item in items:
        alerta = Alerta(
            title=item.get("title"),
            description=item.get("description"),
            source_type=item.get("source_type"),
            category=item.get("category"),
            country=item.get("country"),
            source_url=item.get("source_url"),
            institution=item.get("institution"),
            presentation_date=item.get("presentation_date"),
        )
        try:
            session.add(alerta)
            session.commit()
            saved_count += 1
        except IntegrityError:
            session.rollback()
            duplicate_count += 1

    print(f"[{source_name}] Guardado: {saved_count} | Duplicados: {duplicate_count}")

def main():
    asyncio.run(run_scrapers())

if __name__ == "__main__":
    main()
