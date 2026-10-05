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
    "Limpieza",
    "Tarjeta de Credito",
    "Compras / Varios",
    "Otros",
]

MESES_NOMBRES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


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


# Cargar todos los gastos de la base de datos
df_all_expenses = load_data()

# -------------------------------------------------------------
# Formulario para registrar un nuevo gasto
# -------------------------------------------------------------
with st.form("expense_form", clear_on_submit=True):
  col1, col2 = st.columns(2)

  with col1:
    fecha = st.date_input("Fecha", value=datetime.now().date())
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

# -------------------------------------------------------------
# Barra Lateral (Sidebar): Filtros de Mes y Año
# -------------------------------------------------------------
st.sidebar.header("🔍 Filtro de Período")

# Convertir la columna fecha a datetime para filtrado si existen registros
if not df_all_expenses.empty:
  df_all_expenses["date_dt"] = pd.to_datetime(df_all_expenses["date"])
  years_available = sorted(
      df_all_expenses["date_dt"].dt.year.unique(), reverse=True
  )
  current_year = datetime.now().year
  if current_year not in years_available:
    years_available.insert(0, current_year)
else:
  years_available = [datetime.now().year]

selected_year = st.sidebar.selectbox("Año", options=years_available, index=0)

current_month = datetime.now().month
selected_month_name = st.sidebar.selectbox(
    "Mes",
    options=list(MESES_NOMBRES.values()),
    index=current_month - 1,  # Mes actual por defecto
)

# Convertir el nombre del mes seleccionado a su número (1..12)
selected_month = [
    num for num, name in MESES_NOMBRES.items() if name == selected_month_name
][0]

# Filtrar los datos según el año y mes seleccionados
if not df_all_expenses.empty:
  df_filtered = df_all_expenses[
      (df_all_expenses["date_dt"].dt.year == selected_year)
      & (df_all_expenses["date_dt"].dt.month == selected_month)
  ].copy()
else:
  df_filtered = pd.DataFrame(
      columns=["id", "date", "category", "amount", "note"]
  )

# -------------------------------------------------------------
# Visualización de datos filtrados
# -------------------------------------------------------------
st.subheader(f"📅 Gastos de {selected_month_name} {selected_year}")

if not df_filtered.empty:
  # Asegurar que el monto sea numérico
  df_filtered["amount"] = pd.to_numeric(
      df_filtered["amount"], errors="coerce"
  ).fillna(0)
  total_gasto = df_filtered["amount"].sum()

  st.metric(
      label=f"Total Gastado en {selected_month_name}", value=f"${total_gasto:.2f}"
  )

  # Exportación de datos filtrados
  col_export1, col_export2 = st.columns(2)

  csv_data = df_filtered.rename(
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
      file_name=f"gastos_{selected_year}_{selected_month:02d}.csv",
      mime="text/csv",
      use_container_width=True,
  )

  excel_buffer = io.BytesIO()
  with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    df_filtered.rename(
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
      file_name=f"gastos_{selected_year}_{selected_month:02d}.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      use_container_width=True,
  )

  st.divider()

  # Resumen por categoría
  st.subheader("📊 Gastos por Categoría")
  cat_summary = (
      df_filtered.groupby("category")["amount"]
      .sum()
      .reset_index()
      .rename(columns={"category": "Categoría", "amount": "Monto ($)"})
  )
  cat_summary["Monto ($)"] = cat_summary["Monto ($)"].apply(
      lambda x: f"${x:.2f}"
  )
  st.dataframe(cat_summary, hide_index=True, use_container_width=True)

  # Historial de registros del mes
  st.subheader("📋 Historial de Gastos")
  for _, row in df_filtered.iterrows():
    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 3, 1])
    c1.write(f"**{row['date']}**")
    c2.write(row["category"])
    c3.write(f"${row['amount']:.2f}")
    c4.write(row["note"] if row["note"] else "-")

    if c5.button("🗑️", key=f"del_{row['id']}"):
      delete_expense(row["id"])

else:
  st.info(
      f"No hay gastos registrados para {selected_month_name} de {selected_year}."
  )
