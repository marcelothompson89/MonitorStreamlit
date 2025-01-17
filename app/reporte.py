import streamlit as st
import sys
import os
import datetime
from sqlalchemy import create_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from database.models import Alerta, User, Keyword

# Inicializar estado para el timestamp de la base de datos
if "db_last_modified" not in st.session_state:
    st.session_state.db_last_modified = None

# Función para verificar cambios en la base de datos
def check_db_update(db_path):
    """Verifica si el archivo SQLite ha cambiado."""
    try:
        last_modified = os.path.getmtime(db_path)  # Timestamp de última modificación
        if st.session_state.db_last_modified is None:
            st.session_state.db_last_modified = last_modified
            return False  # No hay cambios
        elif last_modified > st.session_state.db_last_modified:
            st.session_state.db_last_modified = last_modified
            return True  # Se detectaron cambios
    except FileNotFoundError:
        st.error("El archivo de la base de datos no existe.")
        return False
    return False

# Fragmento que maneja la recarga manual y automática
@st.fragment
def auto_reload_fragment(db_path):
    # Verificar si la base de datos ha cambiado
    if check_db_update(db_path):
        st.warning("Se detectaron cambios en la base de datos. Recargando la app...")
        st.rerun()

    # Botón para recargar manualmente
    if st.button("Forzar Recarga"):
        st.session_state.db_last_modified = os.path.getmtime(db_path)
        st.rerun()

def main():
    # Ruta al archivo SQLite
    db_path = "./alerts2.db"

    # Diseño con columnas para el título y el botón de recarga
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title("Listado de Alertas")
    with col2:
        # Fragmento de recarga
        auto_reload_fragment(db_path)

    session = SessionLocal()

    # ----------------------------------------------------------------
    # Barra lateral
    # ----------------------------------------------------------------
    st.sidebar.header("Filtros de búsqueda")

    # 1. Seleccionar usuario
    users = session.query(User).all()
    user_options = [u.email for u in users]
    user_options.insert(0, "<Seleccionar usuario>")
    selected_user_email = st.sidebar.selectbox("Usuario:", user_options)

    user = None
    selected_keywords = []
    if selected_user_email != "<Seleccionar usuario>":
        user = session.query(User).filter(User.email == selected_user_email).first()

    # 2. Palabras clave
    if user:
        user_keywords = session.query(Keyword).filter(Keyword.user_id == user.id).all()
        keywords_list = [kw.word for kw in user_keywords]

        if keywords_list:
            keywords_list.insert(0, "Seleccionar todas")
            selected_keywords = st.sidebar.multiselect(
                "Palabras clave:",
                options=keywords_list,
                default=[]
            )
            if "Seleccionar todas" in selected_keywords:
                selected_keywords = keywords_list[1:]  # Excluir "Seleccionar todas"
        else:
            st.sidebar.info("No hay palabras clave para este usuario.")

    # 3. Filtro por institución
    all_institutions = sorted({a.institution for a in session.query(Alerta).all() if a.institution})
    all_institutions.insert(0, "Todas")
    selected_institution = st.sidebar.selectbox("Institución:", all_institutions)

    # 4. Filtro por país
    all_countries = sorted({a.country for a in session.query(Alerta).all() if a.country})
    all_countries.insert(0, "Todos")
    selected_country = st.sidebar.selectbox("País:", all_countries)

    # 5. Filtro por rango de fechas
    valid_dates = [a.presentation_date for a in session.query(Alerta).all() if a.presentation_date]
    if valid_dates:
        min_date = min(valid_dates).date()
        max_date = max(valid_dates).date()
    else:
        min_date = datetime.date(2000, 1, 1)
        max_date = datetime.date.today()

    date_range = st.sidebar.date_input(
        "Rango de fechas:",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = (min_date, max_date)

    # 6. Búsqueda por texto
    search_text = st.sidebar.text_input("Buscar por título o descripción:")

    # ----------------------------------------------------------------
    # Aplicar filtros
    # ----------------------------------------------------------------
    all_alertas = session.query(Alerta).order_by(Alerta.presentation_date.desc()).all()
    filtered_alertas = [
        alerta for alerta in all_alertas
        if (selected_institution == "Todas" or alerta.institution == selected_institution)
        and (selected_country == "Todos" or alerta.country == selected_country)
        and (not alerta.presentation_date or (start_date <= alerta.presentation_date.date() <= end_date))
        and (not search_text or search_text.lower() in (alerta.title or "").lower() or search_text.lower() in (alerta.description or "").lower())
        and (not selected_keywords or any(k.lower() in (alerta.title or "").lower() or k.lower() in (alerta.description or "").lower() for k in selected_keywords))
    ]

    # ----------------------------------------------------------------
    # Mostrar resultados
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
