from datetime import datetime
import pandas as pd
import streamlit as st
from supabase import create_client

# Configuración de la página
st.set_page_config(
    page_title="Rastreador de Gastos", page_icon="💰", layout="centered"
)

st.title("💰 Rastreador de Gastos")


# Conexión a Supabase
@st.cache_resource
def init_supabase():
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


supabase = init_supabase()


def load_data():
  """Carga los gastos desde Supabase."""
  try:
    response = (
        supabase.table("expenses")
        .select("*")
        .order("date", desc=True)
        .execute()
    )
    data = response.data
    if data:
      df = pd.DataFrame(data)
      df = df.rename(
          columns={
              "date": "Fecha",
              "category": "Categoría",
              "amount": "Monto",
              "note": "Nota",
          }
      )
      return df[["Fecha", "Categoría", "Monto", "Nota"]]
    else:
      return pd.DataFrame(columns=["Fecha", "Categoría", "Monto", "Nota"])
  except Exception as e:
    st.error(f"Error al cargar datos: {e}")
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
    new_expense = {
        "date": fecha.strftime("%Y-%m-%d"),
        "category": categoria.strip().capitalize(),
        "amount": monto,
        "note": nota.strip(),
    }

    try:
      supabase.table("expenses").insert(new_expense).execute()
      st.success("¡Gasto guardado con éxito!")
      st.rerun()
    except Exception as e:
      st.error(f"Error al guardar: {e}")
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
