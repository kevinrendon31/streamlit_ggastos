from datetime import datetime
import io
import pandas as pd
import streamlit as st
from supabase import create_client

# Configuración de la página
st.set_page_config(
    page_title="Rastreador de Gastos", page_icon="💰", layout="centered"
)

st.title("💰 Rastreador de Gastos")

# Lista estandarizada de categorías
CATEGORIAS_ESTANDAR = [
    "Alimentación",
    "Transporte",
    "Renta",
    "Internet",
    "Electricidad",
    "Mascota",
    "Salud y Cuidado Personal",
    "Educación",
    "Comida fuera de casa",
    "Compras / Varios",
    "Otros",
]


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
        supabase.from_("expenses")
        .select("*")
        .order("date", desc=True)
        .execute()
    )
    data = response.data
    if data:
      return pd.DataFrame(data)
    else:
      return pd.DataFrame(
          columns=["id", "date", "category", "amount", "note"]
      )
  except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    return pd.DataFrame(columns=["id", "date", "category", "amount", "note"])


def delete_expense(expense_id):
  """Elimina un gasto por su ID en Supabase."""
  try:
    supabase.from_("expenses").delete().eq("id", expense_id).execute()
    st.success("Gasto eliminado correctamente.")
    st.rerun()
  except Exception as e:
    st.error(f"Error al eliminar: {e}")


df_expenses = load_data()

# Formulario para registrar gasto
with st.form("expense_form", clear_on_submit=True):
  col1, col2 = st.columns(2)

  with col1:
    fecha = st.date_input("Fecha", value=datetime.now().date())
    # Lista desplegable estandarizada
    categoria = st.selectbox("Categoría", options=CATEGORIAS_ESTANDAR)

  with col2:
    monto = st.number_input("Monto ($)", min_value=0.0, step=0.5, format="%.2f")
    nota = st.text_input("Nota", placeholder="Ej. Almuerzo")

  submit_button = st.form_submit_button("Agregar Gasto")

if submit_button:
  if monto > 0:
    new_expense = {
        "date": fecha.strftime("%Y-%m-%d"),
        "category": categoria,
        "amount": monto,
        "note": nota.strip(),
    }

    try:
      supabase.from_("expenses").insert(new_expense).execute()
      st.success("¡Gasto guardado con éxito!")
      st.rerun()
    except Exception as e:
      st.error(f"Error al guardar: {e}")
  else:
    st.warning("Por favor ingresa un monto mayor a 0.")

st.divider()

if not df_expenses.empty:
  # Asegurar que el monto sea numérico
  df_expenses["amount"] = pd.to_numeric(
      df_expenses["amount"], errors="coerce"
  ).fillna(0)
  total_gasto = df_expenses["amount"].sum()

  st.metric(label="Total Gasto Acumulado", value=f"${total_gasto:.2f}")

  # -------------------------------------------------------------
  # Botón para Descargar Gastos (CSV y Excel)
  # -------------------------------------------------------------
  col_export1, col_export2 = st.columns(2)

  # Exportar a CSV
  csv_data = df_expenses.rename(
      columns={
          "date": "Fecha",
          "category": "Categoría",
          "amount": "Monto",
          "note": "Nota",
      }
  )[["Fecha", "Categoría", "Monto", "Nota"]].to_csv(index=False)

  col_export1.download_button(
      label="📥 Descargar CSV",
      data=csv_data,
      file_name=f"gastos_{datetime.now().strftime('%Y%m%d')}.csv",
      mime="text/csv",
      use_container_width=True,
  )

  # Exportar a Excel
  excel_buffer = io.BytesIO()
  with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    df_expenses.rename(
        columns={
            "date": "Fecha",
            "category": "Categoría",
            "amount": "Monto",
            "note": "Nota",
        }
    )[["Fecha", "Categoría", "Monto", "Nota"]].to_excel(
        writer, index=False, sheet_name="Gastos"
    )

  col_export2.download_button(
      label="📊 Descargar Excel",
      data=excel_buffer.getvalue(),
      file_name=f"gastos_{datetime.now().strftime('%Y%m%d')}.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      use_container_width=True,
  )

  st.divider()

  st.subheader("📊 Gastos por Categoría")
  cat_summary = (
      df_expenses.groupby("category")["amount"]
      .sum()
      .reset_index()
      .rename(columns={"category": "Categoría", "amount": "Monto ($)"})
  )
  st.dataframe(cat_summary, hide_index=True, use_container_width=True)

  st.subheader("📋 Historial de Gastos")

  # Vista con opción de borrar cada registro
  for _, row in df_expenses.iterrows():
    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 3, 1])
    c1.write(f"**{row['date']}**")
    c2.write(row["category"])
    c3.write(f"${row['amount']:.2f}")
    c4.write(row["note"] if row["note"] else "-")

    if c5.button("🗑️", key=f"del_{row['id']}"):
      delete_expense(row["id"])

else:
  st.info("No hay gastos registrados aún.")
