import pandas as pd
from datetime import datetime
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuración de la página
st.set_page_config(
    page_title="Rastreador de Gastos", page_icon="💰", layout="centered"
)

st.title("💰 Rastreador de Gastos")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)


def load_data():
  """Carga los gastos desde Google Sheets."""
  try:
    data = conn.read(ttl="0d")  # Cargar datos siempre actualizados
    return (
        data
        if not data.empty
        else pd.DataFrame(columns=["Fecha", "Categoría", "Monto", "Nota"])
    )
  except Exception:
    return pd.DataFrame(columns=["Fecha", "Categoría", "Monto", "Nota"])


df_expenses = load_data()

# Formulario para registrar gasto
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
    new_row = pd.DataFrame([{
        "Fecha": fecha.strftime("%Y-%m-%d"),
        "Categoría": categoria.strip().capitalize(),
        "Monto": monto,
        "Nota": nota.strip(),
    }])

    # Combinar datos existentes con la nueva fila
    updated_df = pd.concat([df_expenses, new_row], ignore_index=True)

    # Guardar en Google Sheets usando .create() para evitar UnsupportedOperationError
    conn.create(data=updated_df)
    st.success("¡Gasto guardado con éxito en Google Sheets!")
    st.rerun()
  else:
    st.warning("Por favor ingresa una categoría válida y un monto mayor a 0.")

# Mostrar métricas y tablas
st.divider()

if not df_expenses.empty and "Monto" in df_expenses.columns:
  df_expenses["Monto"] = pd.to_numeric(
      df_expenses["Monto"], errors="coerce"
  ).fillna(0)
  total_gasto = df_expenses["Monto"].sum()
  st.metric(label="Total Gasto Acumulado", value=f"${total_gasto:.2f}")

  st.subheader("📊 Gastos por Categoría")
  cat_summary = df_expenses.groupby("Categoría")["Monto"].sum().reset_index()
  st.dataframe(cat_summary, hide_index=True, use_container_width=True)

  st.subheader("📋 Historial de Gastos")
  st.dataframe(df_expenses, hide_index=True, use_container_width=True)
else:
  st.info("No hay gastos registrados aún.")
