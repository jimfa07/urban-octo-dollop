
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

# Archivos
DATA_FILE = "registro_data.pkl"
DEPOSITS_FILE = "registro_depositos.pkl"
DEBIT_NOTES_FILE = "registro_notas_debito.pkl"

st.set_page_config(page_title="Registro Proveedores y DepÃ³sitos", layout="wide")
st.title("Registro de Proveedores - Producto Pollo")

# Listas
proveedores = ["LIRIS SA", "Gallina 1", "Monze Anzules", "Medina"]
tipos_documento = ["Factura", "Nota de dÃ©bito", "Nota de crÃ©dito"]
agencias = [
    "Cajero AutomÃ¡tico Pichincha", "Cajero AutomÃ¡tico PacÃ­fico",
    "Cajero AutomÃ¡tico Guayaquil", "Cajero AutomÃ¡tico Bolivariano",
    "Banco Pichincha", "Banco del Pacifico", "Banco de Guayaquil",
    "Banco Bolivariano"
]

# Inicializar estados
if "data" not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state.data = pd.read_pickle(DATA_FILE)
        st.session_state.data["Fecha"] = pd.to_datetime(
            st.session_state.data["Fecha"], errors="coerce").dt.date
    else:
        st.session_state.data = pd.DataFrame(columns=[
            "NÂº", "Fecha", "Proveedor", "Producto", "Cantidad",
            "Peso Salida (kg)", "Peso Entrada (kg)", "Tipo Documento",
            "Cantidad de gavetas", "Precio Unitario ($)", "Promedio",
            "Kilos Restantes", "Libras Restantes", "Total ($)",
            "Monto DepÃ³sito", "Saldo diario", "Saldo Acumulado"
        ])
        fila_inicial = {col: None for col in st.session_state.data.columns}
        fila_inicial["Saldo diario"] = 0.00
        fila_inicial["Saldo Acumulado"] = -35
        st.session_state.data = pd.concat(
            [pd.DataFrame([fila_inicial]), st.session_state.data], ignore_index=True
        )

if "df" not in st.session_state:
    if os.path.exists(DEPOSITS_FILE):
        st.session_state.df = pd.read_pickle(DEPOSITS_FILE)
        st.session_state.df["Fecha"] = pd.to_datetime(
            st.session_state.df["Fecha"], errors="coerce").dt.date
    else:
        st.session_state.df = pd.DataFrame(columns=[
            "Fecha", "Empresa", "Agencia", "Monto", "Documento", "N"
        ])

if "notas" not in st.session_state:
    if os.path.exists(DEBIT_NOTES_FILE):
        st.session_state.notas = pd.read_pickle(DEBIT_NOTES_FILE)
    else:
        st.session_state.notas = pd.DataFrame(columns=[
            "Fecha", "Libras calculadas", "Descuento", "Descuento posible", "Descuento real"
        ])

# Sidebar - Registro de DepÃ³sitos
st.sidebar.header("Registro de DepÃ³sitos")
with st.sidebar.form("registro_form"):
    fecha_d = st.date_input("Fecha del registro", value=datetime.today(), key="fecha_d")
    empresa = st.selectbox("Empresa (Proveedor)", proveedores, key="empresa")
    agencia = st.selectbox("Agencia", agencias, key="agencia")
    monto = st.number_input("Monto", min_value=0.0, format="%.2f", key="monto")
    submit_d = st.form_submit_button("Agregar DepÃ³sito")

if submit_d:
    documento = "DepÃ³sito" if "Cajero" in agencia else "Transferencia"
    df_actual = st.session_state.df
    coincidencia = df_actual[
        (df_actual["Fecha"] == fecha_d) & (df_actual["Empresa"] == empresa)
    ]
    numero = coincidencia["N"].iloc[0] if not coincidencia.empty else f"{df_actual['Fecha'].nunique() + 1:02}"

    nuevo_registro = {
        "Fecha": fecha_d,
        "Empresa": empresa,
        "Agencia": agencia,
        "Monto": monto,
        "Documento": documento,
        "N": numero
    }

    st.session_state.df = pd.concat([df_actual, pd.DataFrame([nuevo_registro])], ignore_index=True)
    st.session_state.df.to_pickle(DEPOSITS_FILE)
    st.success("DepÃ³sito agregado exitosamente.")

# Eliminar depÃ³sito
st.sidebar.subheader("Eliminar un DepÃ³sito")
if not st.session_state.df.empty:
    st.session_state.df["Mostrar"] = st.session_state.df.apply(
        lambda row: f"{row['Fecha']} - {row['Empresa']} - ${row['Monto']:.2f}", axis=1
    )
    deposito_a_eliminar = st.sidebar.selectbox(
        "Selecciona un depÃ³sito a eliminar", st.session_state.df["Mostrar"]
    )
    if st.sidebar.button("Eliminar depÃ³sito seleccionado"):
        index_eliminar = st.session_state.df[st.session_state.df["Mostrar"] == deposito_a_eliminar].index[0]
        st.session_state.df.drop(index=index_eliminar, inplace=True)
        st.session_state.df.reset_index(drop=True, inplace=True)
        st.session_state.df.to_pickle(DEPOSITS_FILE)
        st.sidebar.success("DepÃ³sito eliminado correctamente.")
else:
    st.sidebar.write("No hay depÃ³sitos para eliminar.")

# Registro de Proveedores
st.subheader("Registro de Proveedores")
with st.form("formulario"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fecha = st.date_input("Fecha", value=datetime.today())
        proveedor = st.selectbox("Proveedor", proveedores)
    with col2:
        cantidad = st.number_input("Cantidad", min_value=0, step=1)
        peso_salida = st.number_input("Peso Salida (kg)", min_value=0.0, step=0.1)
    with col3:
        peso_entrada = st.number_input("Peso Entrada (kg)", min_value=0.0, step=0.1)
        documento = st.selectbox("Tipo Documento", tipos_documento)
    with col4:
        gavetas = st.number_input("Cantidad de gavetas", min_value=0, step=1)
        precio_unitario = st.number_input("Precio Unitario ($)", min_value=0.0, step=0.01)

    enviar = st.form_submit_button("Agregar Registro")

if enviar:
    df = st.session_state.data.copy()
    producto = "Pollo"
    kilos_restantes = peso_salida - peso_entrada
    libras_restantes = kilos_restantes * 2.20462
    promedio = libras_restantes / cantidad if cantidad != 0 else 0
    total = libras_restantes * precio_unitario
    enumeracion = df["Fecha"].nunique() + 1 if fecha not in df["Fecha"].dropna().values else df[df["Fecha"] == fecha]["NÂº"].iloc[0]

    depositos = st.session_state.df.copy()
    monto_deposito = depositos[
        (depositos["Fecha"] == fecha) & (depositos["Empresa"] == proveedor)
    ]["Monto"].sum()
    saldo_diario = monto_deposito - total
    saldo_acumulado = df["Saldo Acumulado"].dropna().iloc[-1] + saldo_diario if df["Saldo Acumulado"].dropna().shape[0] > 0 else -35 + saldo_diario

    nueva_fila = {
        "NÂº": enumeracion,
        "Fecha": fecha,
        "Proveedor": proveedor,
        "Producto": producto,
        "Cantidad": cantidad,
        "Peso Salida (kg)": peso_salida,
        "Peso Entrada (kg)": peso_entrada,
        "Tipo Documento": documento,
        "Cantidad de gavetas": gavetas,
        "Precio Unitario ($)": precio_unitario,
        "Promedio": promedio,
        "Kilos Restantes": kilos_restantes,
        "Libras Restantes": libras_restantes,
        "Total ($)": total,
        "Monto DepÃ³sito": monto_deposito,
        "Saldo diario": saldo_diario,
        "Saldo Acumulado": saldo_acumulado
    }

    st.session_state.data = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    st.success("Registro agregado correctamente")
    st.session_state.data.to_pickle(DATA_FILE)
