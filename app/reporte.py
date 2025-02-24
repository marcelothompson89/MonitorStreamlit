import streamlit as st
import sys
import os
import datetime
from sqlalchemy import or_
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from database.models import Alerta, User, Keyword

# Inicializar estado para el timestamp de la base de datos
if "db_last_modified" not in st.session_state:
    st.session_state.db_last_modified = None

# Función para verificar cambios en el archivo SQLite
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

# Fragmento para recarga automática (sin botón de forzar recarga)
@st.fragment
def auto_reload_fragment(db_path):
    if check_db_update(db_path):
        st.warning("Se detectaron cambios en la base de datos. Recargando la app...")
        st.rerun()

def main():
    # Ruta al archivo SQLite
    db_path = "./alerts2.db"

    # Diseño de la cabecera
    col1, _ = st.columns([8, 2])
    with col1:
        st.title("Listado de Alertas")

    # Llamar al fragmento de recarga automática
    auto_reload_fragment(db_path)

    session = SessionLocal()

    # ----------------------------------------------------------------
    # Barra lateral: Filtros de búsqueda
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
    all_institutions = session.query(Alerta.institution).distinct().all()
    all_institutions = sorted([inst[0] for inst in all_institutions if inst[0]])
    all_institutions.insert(0, "Todas")
    selected_institution = st.sidebar.selectbox("Institución:", all_institutions)

    # 4. Filtro por país
    all_countries = session.query(Alerta.country).distinct().all()
    all_countries = sorted([country[0] for country in all_countries if country[0]])
    all_countries.insert(0, "Todos")
    selected_country = st.sidebar.selectbox("País:", all_countries)

    # 5. Filtro por rango de fechas (sin restricciones en el widget)
    valid_dates = session.query(Alerta.presentation_date)\
                         .filter(Alerta.presentation_date.isnot(None)).all()
    valid_dates = [d[0] for d in valid_dates]
    if valid_dates:
        min_date = min(valid_dates).date()
        max_date = max(valid_dates).date()
    else:
        min_date = datetime.date(2000, 1, 1)
        max_date = datetime.date.today()

    date_range = st.sidebar.date_input(
        "Rango de fechas:",
        value=[min_date, max_date]
        # Se eliminan min_value=min_date y max_value=max_date
        # para permitir elegir cualquier fecha
    )
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = (min_date, max_date)

    # 6. Búsqueda por texto
    search_text = st.sidebar.text_input("Buscar por título o descripción:")

    # ----------------------------------------------------------------
    # Construir la consulta SQL aplicando los filtros
    # ----------------------------------------------------------------
    query = session.query(Alerta)

    if selected_institution != "Todas":
        query = query.filter(Alerta.institution == selected_institution)

    if selected_country != "Todos":
        query = query.filter(Alerta.country == selected_country)

    # Filtrado por rango de fechas, incluyendo registros con fecha nula
    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
    query = query.filter(
        or_(
            Alerta.presentation_date == None,
            Alerta.presentation_date.between(start_datetime, end_datetime)
        )
    )

    # Búsqueda por texto en título o descripción
    if search_text:
        query = query.filter(
            or_(
                Alerta.title.ilike(f"%{search_text}%"),
                Alerta.description.ilike(f"%{search_text}%")
            )
        )

    # Filtrado por palabras clave (si se seleccionaron)
    if selected_keywords:
        keyword_conditions = [
            or_(
                Alerta.title.ilike(f"%{kw}%"),
                Alerta.description.ilike(f"%{kw}%")
            )
            for kw in selected_keywords
        ]
        query = query.filter(or_(*keyword_conditions))

    # Ordenar por fecha de presentación (descendente)
    query = query.order_by(Alerta.presentation_date.desc())

    # ----------------------------------------------------------------
    # Paginación
    # ----------------------------------------------------------------
    page_size = st.sidebar.number_input("Registros por página", min_value=10, max_value=100, value=50)
    page = st.sidebar.number_input("Página", min_value=1, value=1)

    total_alertas = query.count()
    query = query.limit(page_size).offset((page - 1) * page_size)
    alertas = query.all()

    st.subheader(f"{total_alertas} resultado(s) encontrado(s)")

    # ----------------------------------------------------------------
    # Mostrar resultados
    # ----------------------------------------------------------------
    if alertas:
        for alerta in alertas:
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
