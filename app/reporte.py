# app/reporte.py
import streamlit as st
import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from database.models import Alerta, User, Keyword

def main():
    st.title("Listado de Alertas")

    session = SessionLocal()

    # ----------------------------------------------------------------
    # 4. Obtener todas las alertas
    # ----------------------------------------------------------------
    all_alertas = session.query(Alerta).order_by(Alerta.presentation_date.desc()).all()

    # ----------------------------------------------------------------
    # 1. Seleccionar usuario
    # ----------------------------------------------------------------
    users = session.query(User).all()
    user_options = [u.email for u in users]
    user_options.insert(0, "<Seleccionar usuario>")  # Opción inicial

    selected_user_email = st.selectbox(
        "Usuario para administrar palabras clave:",
        user_options
    )
    user = None
    selected_keywords = []
    if selected_user_email != "<Seleccionar usuario>":
        user = session.query(User).filter(User.email == selected_user_email).first()

    # ----------------------------------------------------------------
    # 2. Columnas: izquierda (lista keywords), derecha (agregar keyword)
    # ----------------------------------------------------------------
    col_keywords, col_add = st.columns([3, 1])

    # Mostrar las palabras clave en un desplegable
    with col_keywords:
        if user:
            st.subheader(f"Palabras clave de {user.email}")

            # Obtener todas las palabras clave del usuario
            user_keywords = session.query(Keyword).filter(Keyword.user_id == user.id).all()
            keywords_list = [kw.word for kw in user_keywords]

            if keywords_list:
                # Añadir opción "Seleccionar todas"
                select_all_option = "Seleccionar todas"
                keywords_list.insert(0, select_all_option)

                # Desplegable de selección múltiple
                selected_keywords = st.multiselect(
                    "Selecciona palabras clave para filtrar:",
                    options=keywords_list,
                    default=[]  # Por defecto, ninguna seleccionada
                )

                # Si el usuario selecciona "Seleccionar todas", selecciona todo automáticamente
                if select_all_option in selected_keywords:
                    selected_keywords = keywords_list[1:]  # Excluye "Seleccionar todas"

                st.write("Palabras seleccionadas:", ", ".join(selected_keywords))
            else:
                st.info("No hay palabras clave para este usuario.")
        else:
            st.info("Por favor, selecciona un usuario para administrar sus palabras clave.")

    # ----------------------------------------------------------------
    # 5. Filtro por Institución
    # ----------------------------------------------------------------
    all_institutions = sorted({a.institution for a in all_alertas if a.institution})
    all_institutions.insert(0, "Todas")
    selected_institution = st.selectbox("Filtrar por institución:", all_institutions)

    # ----------------------------------------------------------------
    # 6. Filtro por País
    # ----------------------------------------------------------------
    all_countries = sorted({a.country for a in all_alertas if a.country})
    all_countries.insert(0, "Todos")
    selected_country = st.selectbox("Filtrar por país:", all_countries)

    # ----------------------------------------------------------------
    # 7. Filtro Rango de Fechas
    # ----------------------------------------------------------------
    valid_dates = [a.presentation_date for a in all_alertas if a.presentation_date]
    if valid_dates:
        min_date = min(valid_dates).date()
        max_date = max(valid_dates).date()
    else:
        min_date = datetime.date(2000, 1, 1)
        max_date = datetime.date.today()

    st.write("Filtrar por rango de fechas:")
    date_range = st.date_input(
        "Selecciona fecha inicial y final",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = (min_date, max_date)

    # ----------------------------------------------------------------
    # 8. Búsqueda por Título/Descripción
    # ----------------------------------------------------------------
    search_text = st.text_input("Buscar por título o descripción", value="")

    # ----------------------------------------------------------------
    # 9. Aplicar Filtros
    # ----------------------------------------------------------------
    filtered_alertas = [
        alerta for alerta in all_alertas
        if (selected_institution == "Todas" or alerta.institution == selected_institution)
        and (selected_country == "Todos" or alerta.country == selected_country)
        and (not alerta.presentation_date or (start_date <= alerta.presentation_date.date() <= end_date))
        and (not search_text or search_text.lower() in (alerta.title or "").lower() or search_text.lower() in (alerta.description or "").lower())
        and (not selected_keywords or any(k.lower() in (alerta.title or "").lower() or k.lower() in (alerta.description or "").lower() for k in selected_keywords))
    ]

    # ----------------------------------------------------------------
    # 10. Mostrar resultados
    # ----------------------------------------------------------------
    if filtered_alertas:
        st.subheader(f"{len(filtered_alertas)} resultado(s) encontrado(s)")
        for alerta in filtered_alertas:
            st.markdown("---")
            st.write(f"**Título**: {alerta.title}")
            st.write(f"Fecha: {alerta.presentation_date}")
            st.write(f"Tipo: {alerta.source_type}")
            st.write(f"Categoría: {alerta.category}")
            st.write(f"País: {alerta.country}")
            st.write(f"Institución: {alerta.institution}")
            if alerta.source_url:
                st.write(f"[Ver Alerta]({alerta.source_url})", unsafe_allow_html=True)
    else:
        st.write("No hay alertas disponibles con los filtros seleccionados.")

    session.close()

if __name__ == "__main__":
    main()