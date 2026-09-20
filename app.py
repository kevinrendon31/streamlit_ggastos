import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Rastreador de Gastos", page_icon="💰", layout="centered"
)

DB_FILE = "expenses.db"


def init_db():
    """Crea la base de datos SQLite si no existe."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        note TEXT
    )
    """)
    conn.commit()
    conn.close()


def load_expenses():
    """Carga los gastos desde la base de datos."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT id, date AS Fecha, category AS Categoría, amount AS Monto, note AS Nota FROM expenses ORDER BY date DESC",
        conn,
    )
    conn.close()
    return df


def save_expense(date, category, amount, note):
    """Guarda un nuevo gasto en la base de datos."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)",
        (date, category, amount, note),
    )
    conn.commit()
    conn.close()


# Inicializar la base de datos
init_db()

# Título e Interfaz
st.title("💰 Rastreador de Gastos")

# Formulario de ingreso
with st.form("expense_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Fecha", value=datetime.now().date())
        categoria = st.text_input("Categoría", placeholder="Ej. Comida")

    with col2:
        monto = st.number_input("Monto ($)", min_value=0.0, step=0.5, format="%.2f")
        nota = st.text_input("Nota", placeholder="Ej. Almuerzo")

    submit_button = st.form_submit_button("Agregar Gasto")

if submit_button:
    if categoria.strip() and monto > 0:
        save_expense(
            fecha.strftime("%Y-%m-%d"),
            categoria.strip().capitalize(),
            monto,
            nota.strip(),
        )
        st.success("¡Gasto guardado con éxito!")
        st.rerun()
    else:
        st.warning(
            "Por favor ingresa una categoría válida y un monto mayor a 0."
        )

# Cargar datos actuales
df_expenses = load_expenses()

# Mostrar métricas
st.divider()
total_gasto = df_expenses["Monto"].sum() if not df_expenses.empty else 0.0
st.metric(label="Total Gasto Acumulado", value=f"${total_gasto:.2f}")

# Mostrar gastos por categoría
if not df_expenses.empty:
    st.subheader("📊 Gastos por Categoría")
    cat_summary = (
        df_expenses.groupby("Categoría")["Monto"].sum().reset_index()
    )
    st.dataframe(cat_summary, hide_index=True, use_container_width=True)

    st.subheader("📋 Historial de Gastos")
    st.dataframe(
        df_expenses[["Fecha", "Categoría", "Monto", "Nota"]],
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("No hay gastos registrados aún.")