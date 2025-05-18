import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

# Archivos
data_file = "registro_data.pkl"
deposits_file = "registro_depositos.pkl"
debit_notes_file = "registro_notas_debito.pkl"

st.set_page_config(page_title="Registro Proveedores y Depósitos", layout="wide")

# Menú lateral de navegación
menu = st.sidebar.selectbox("Seleccionar vista", [
    "Registro", "Reporte Semanal", "Reporte Mensual", "Gráficos"
])

# Listas
proveedores = ["LIRIS SA", "Gallina 1", "Monze Anzules", "Medina"]
tipos_documento = ["Factura", "Nota de débito", "Nota de crédito"]
agencias = [
    "Cajero Automático Pichincha", "Cajero Automático Pacífico",
    "Cajero Automático Guayaquil", "Cajero Automático Bolivariano",
    "Banco Pichincha", "Banco del Pacifico", "Banco de Guayaquil",
    "Banco Bolivariano"
]

# Inicializar estados
def cargar_datos():
    if "data" not in st.session_state:
        if os.path.exists(data_file):
            st.session_state.data = pd.read_pickle(data_file)
            st.session_state.data["Fecha"] = pd.to_datetime(
                st.session_state.data["Fecha"], errors="coerce"
            ).dt.date
        else:
            columnas = ["Nº", "Fecha", "Proveedor", "Producto", "Cantidad", "Peso Salida (kg)",
                        "Peso Entrada (kg)", "Tipo Documento", "Cantidad de gavetas",
                        "Precio Unitario ($)", "Promedio", "Kilos Restantes",
                        "Libras Restantes", "Total ($)", "Monto Depósito",
                        "Saldo diario", "Saldo Acumulado"]
            st.session_state.data = pd.DataFrame(columns=columnas)
            fila_inicial = {col: None for col in columnas}
            fila_inicial["Saldo diario"] = 0.00
            fila_inicial["Saldo Acumulado"] = -35
            st.session_state.data = pd.concat([
                pd.DataFrame([fila_inicial]), st.session_state.data
            ], ignore_index=True)

    if "df" not in st.session_state:
        if os.path.exists(deposits_file):
            st.session_state.df = pd.read_pickle(deposits_file)
            st.session_state.df["Fecha"] = pd.to_datetime(
                st.session_state.df["Fecha"], errors="coerce"
            ).dt.date
        else:
            st.session_state.df = pd.DataFrame(columns=[
                "Fecha", "Empresa", "Agencia", "Monto", "Documento", "N"
            ])

    if "notas" not in st.session_state:
        if os.path.exists(debit_notes_file):
            st.session_state.notas = pd.read_pickle(debit_notes_file)
        else:
            st.session_state.notas = pd.DataFrame(columns=[
                "Fecha", "Libras calculadas", "Descuento", "Descuento posible", "Descuento real"
            ])

cargar_datos()

if menu == "Registro":
    st.title("Registro de Proveedores - Producto Pollo")

    # Registro de Depósitos
    st.sidebar.header("Registro de Depósitos")
    with st.sidebar.form("registro_form"):
        fecha_d = st.date_input("Fecha del registro", value=datetime.today(), key="fecha_d")
        empresa = st.selectbox("Empresa (Proveedor)", proveedores, key="empresa")
        agencia = st.selectbox("Agencia", agencias, key="agencia")
        monto = st.number_input("Monto", min_value=0.0, format="%.2f", key="monto")
        submit_d = st.form_submit_button("Agregar Depósito")

    if submit_d:
        documento = "Depósito" if "Cajero" in agencia else "Transferencia"
        df_actual = st.session_state.df
        coincidencia = df_actual[(df_actual["Fecha"] == fecha_d) & (df_actual["Empresa"] == empresa)]
        numero = coincidencia["N"].iloc[0] if not coincidencia.empty else f"{df_actual['Fecha'].nunique() + 1:02}"
        nuevo_registro = {
            "Fecha": fecha_d, "Empresa": empresa, "Agencia": agencia,
            "Monto": monto, "Documento": documento, "N": numero
        }
        st.session_state.df = pd.concat([df_actual, pd.DataFrame([nuevo_registro])], ignore_index=True)
        st.session_state.df.to_pickle(deposits_file)
        st.success("Depósito agregado exitosamente.")

    # Eliminar Depósito
    st.sidebar.subheader("Eliminar un Depósito")
    if not st.session_state.df.empty:
        st.session_state.df["Mostrar"] = st.session_state.df.apply(
            lambda row: f"{row['Fecha']} - {row['Empresa']} - ${row['Monto']:.2f}", axis=1
        )
        deposito_a_eliminar = st.sidebar.selectbox("Selecciona un depósito a eliminar", st.session_state.df["Mostrar"])
        if st.sidebar.button("Eliminar depósito seleccionado"):
            index_eliminar = st.session_state.df[st.session_state.df["Mostrar"] == deposito_a_eliminar].index[0]
            st.session_state.df.drop(index=index_eliminar, inplace=True)
            st.session_state.df.reset_index(drop=True, inplace=True)
            st.session_state.df.to_pickle(deposits_file)
            st.sidebar.success("Depósito eliminado correctamente.")

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
        enumeracion = df["Fecha"].nunique() + 1 if fecha not in df["Fecha"].dropna().values else df[df["Fecha"] == fecha]["Nº"].iloc[0]
        depositos = st.session_state.df.copy()
        monto_deposito = depositos[(depositos["Fecha"] == fecha) & (depositos["Empresa"] == proveedor)]["Monto"].sum()
        saldo_diario = monto_deposito - total
        saldo_acumulado = df["Saldo Acumulado"].dropna().iloc[-1] + saldo_diario if df["Saldo Acumulado"].dropna().shape[0] > 0 else -35 + saldo_diario
        nueva_fila = {
            "Nº": enumeracion, "Fecha": fecha, "Proveedor": proveedor, "Producto": producto, "Cantidad": cantidad,
            "Peso Salida (kg)": peso_salida, "Peso Entrada (kg)": peso_entrada, "Tipo Documento": documento,
            "Cantidad de gavetas": gavetas, "Precio Unitario ($)": precio_unitario, "Promedio": promedio,
            "Kilos Restantes": kilos_restantes, "Libras Restantes": libras_restantes, "Total ($)": total,
            "Monto Depósito": monto_deposito, "Saldo diario": saldo_diario, "Saldo Acumulado": saldo_acumulado
        }
        st.session_state.data = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
        st.session_state.data.to_pickle(data_file)
        st.success("Registro agregado correctamente")

    # Resto de código para Nota de Débito, tablas y descarga (omitir para brevedad)...

elif menu == "Reporte Semanal":
    st.subheader("Reporte Semanal")
    df = st.session_state.data.copy()
    df["Semana"] = pd.to_datetime(df["Fecha"]).dt.to_period("W").astype(str)
    resumen = df.groupby("Semana").agg({
        "Total ($)": "sum", "Monto Depósito": "sum", "Saldo diario": "sum", "Saldo Acumulado": "last"
    }).reset_index()
    resumen.columns = ["Semana", "Total Facturado", "Total Depositado", "Saldo Diario", "Saldo Acumulado"]
    st.dataframe(resumen)

elif menu == "Reporte Mensual":
    st.subheader("Comparativa Mensual de Descuentos")
    notas = st.session_state.notas.copy()
    notas["Mes"] = pd.to_datetime(notas["Fecha"]).dt.to_period("M").astype(str)
    resumen = notas.groupby("Mes").agg({
        "Descuento posible": "sum", "Descuento real": "sum"
    }).reset_index()
    st.dataframe(resumen)

elif menu == "Gráficos":
    st.subheader("Total entregado vs Total depositado por proveedor")
    df = st.session_state.data.copy()
    resumen = df.groupby("Proveedor").agg({
        "Total ($)": "sum", "Monto Depósito": "sum"
    }).reset_index()
    st.bar_chart(resumen.set_index("Proveedor"))
