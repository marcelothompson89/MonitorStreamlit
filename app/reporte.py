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
    if selected_user_email != "<Seleccionar usuario>":
        user = session.query(User).filter(User.email == selected_user_email).first()

    # ----------------------------------------------------------------
    # 2. Columnas: izquierda (lista keywords), derecha (agregar keyword)
    # ----------------------------------------------------------------
    col_keywords, col_add = st.columns([3, 1])

    # Checkbox global para aplicar o no las palabras clave en el filtrado
    apply_keyword_filter = False

    with col_keywords:
        if user:
            st.subheader(f"Palabras clave de {user.email}")
            
            # Activar/Desactivar filtro global por palabras clave
            apply_keyword_filter = st.checkbox("Activar Filtro de Palabras Clave", value=False)

            # Traer todas las keywords del usuario
            user_keywords = session.query(Keyword).filter(
                Keyword.user_id == user.id
            ).all()

            if user_keywords:
                # Mostramos cada palabra clave con un pequeño recuadro
                for kw in user_keywords:
                    with st.container():
                        c1, c2 = st.columns([6, 1])

                        # Texto de la palabra clave
                        c1.markdown(f"**{kw.word}**")

                        # Botón cruz para eliminar
                        if c2.button("❌", key=f"del_{kw.id}"):
                            session.delete(kw)
                            session.commit()
                            st.rerun()
            else:
                st.info("No hay palabras clave para este usuario.")
        else:
            st.info("Por favor, selecciona un usuario para administrar sus palabras clave.")

    # ----------------------------------------------------------------
    # 3. Formulario para agregar nueva palabra (columna derecha)
    # ----------------------------------------------------------------
    with col_add:
        if user:
            st.subheader("Agregar Palabra Clave")
            new_word = st.text_input("", placeholder="Escribe la palabra…")
            if st.button("Agregar"):
                if new_word.strip():
                    new_kw = Keyword(
                        word=new_word.strip(),
                        user_id=user.id
                        # asumiendo que ya no usas 'active' individualmente
                    )
                    session.add(new_kw)
                    session.commit()
                    st.success(f"Palabra clave '{new_word}' agregada.")
                    st.rerun()

    # ----------------------------------------------------------------
    # 4. Obtener todas las alertas
    # ----------------------------------------------------------------
    all_alertas = session.query(Alerta).all()

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
    filtered_alertas = []
    for alerta in all_alertas:
        # Filtro institución
        if selected_institution != "Todas" and alerta.institution != selected_institution:
            continue

        # Filtro país
        if selected_country != "Todos" and alerta.country != selected_country:
            continue

        # Filtro rango de fechas
        if alerta.presentation_date:
            alerta_date = alerta.presentation_date.date()
            if not (start_date <= alerta_date <= end_date):
                continue

        # Filtro de texto
        if search_text:
            s_text_lower = search_text.lower()
            title_lower = (alerta.title or "").lower()
            desc_lower = (alerta.description or "").lower()
            if s_text_lower not in title_lower and s_text_lower not in desc_lower:
                continue

        # Filtro global de palabras clave
        if apply_keyword_filter and user:
            keywords_list = [kw.word.lower() for kw in user.keywords]
            if keywords_list:
                titulo_lower = (alerta.title or "").lower()
                desc_lower = (alerta.description or "").lower()
                # Si no coincide con al menos una keyword, lo descartamos
                if not any(k in titulo_lower or k in desc_lower for k in keywords_list):
                    continue

        filtered_alertas.append(alerta)

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
