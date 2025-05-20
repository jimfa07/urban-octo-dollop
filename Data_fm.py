import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import os
import matplotlib.pyplot as plt

# Archivos
DATA_FILE = "registro_data.pkl"
DEPOSITS_FILE = "registro_depositos.pkl"
DEBIT_NOTES_FILE = "registro_notas_debito.pkl"

st.set_page_config(page_title="Registro Proveedores y Depositos", layout="wide")
st.title("Registro de Proveedores - Producto Pollo")

# Botón para importar CSV
st.markdown("### Importar datos desde CSV")
archivo_csv = st.file_uploader("Selecciona un archivo CSV", type=["csv"])

if archivo_csv is not None:
    try:
        df_csv = pd.read_csv(archivo_csv)
        if "Fecha" in df_csv.columns:
            df_csv["Fecha"] = pd.to_datetime(df_csv["Fecha"], errors="coerce").dt.date
        st.session_state.data = pd.concat([st.session_state.data, df_csv], ignore_index=True)
        st.success("Archivo CSV importado correctamente.")
        st.session_state.data.to_pickle(DATA_FILE)
    except Exception as e:
        st.error(f"Error al importar el archivo: {e}")

# Listas
proveedores = ["LIRIS SA", "Gallina 1", "Monze Anzules", "Medina"]
tipos_documento = ["Factura", "Nota de debito", "Nota de credito"]
agencias = [
    "Cajero Automatico Pichincha", "Cajero Automatico Pacifico",
    "Cajero Automatico Guayaquil", "Cajero Automatico Bolivariano",
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
            "N", "Fecha", "Proveedor", "Producto", "Cantidad",
            "Peso Salida (kg)", "Peso Entrada (kg)", "Tipo Documento",
            "Cantidad de gavetas", "Precio Unitario ($)", "Promedio",
            "Kilos Restantes", "Libras Restantes", "Total ($)",
            "Monto Deposito", "Saldo diario", "Saldo Acumulado"
        ])
        fila_inicial = {col: None for col in st.session_state.data.columns}
        fila_inicial["Saldo diario"] = 0.00
        fila_inicial["Saldo Acumulado"] = -243.30
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

# Navegacion entre secciones
opcion = st.sidebar.selectbox("Selecciona una vista", ["Registro", "Reporte Semanal", "Reporte Mensual", "Graficos"])

if opcion == "Registro":
    # Sidebar - Registro de Depositos
    st.sidebar.header("Registro de Depositos")
    with st.sidebar.form("registro_form"):
        fecha_d = st.date_input("Fecha del registro", value=datetime.today(), key="fecha_d")
        empresa = st.selectbox("Empresa (Proveedor)", proveedores, key="empresa")
        agencia = st.selectbox("Agencia", agencias, key="agencia")
        monto = st.number_input("Monto", min_value=0.0, format="%.2f", key="monto")
        submit_d = st.form_submit_button("Agregar Deposito")

    if submit_d:
        documento = "Deposito" if "Cajero" in agencia else "Transferencia"
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
        st.success("Deposito agregado exitosamente.")

    # Eliminar deposito
    st.sidebar.subheader("Eliminar un Deposito")
    if not st.session_state.df.empty:
        st.session_state.df["Mostrar"] = st.session_state.df.apply(
            lambda row: f"{row['Fecha']} - {row['Empresa']} - ${row['Monto']:.2f}", axis=1
        )
        deposito_a_eliminar = st.sidebar.selectbox(
            "Selecciona un deposito a eliminar", st.session_state.df["Mostrar"]
        )
        if st.sidebar.button("Eliminar deposito seleccionado"):
            index_eliminar = st.session_state.df[st.session_state.df["Mostrar"] == deposito_a_eliminar].index[0]
            st.session_state.df.drop(index=index_eliminar, inplace=True)
            st.session_state.df.reset_index(drop=True, inplace=True)
            st.session_state.df.to_pickle(DEPOSITS_FILE)
            st.sidebar.success("Deposito eliminado correctamente.")
    else:
        st.sidebar.write("No hay depositos para eliminar.")

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
        enumeracion = df["Fecha"].nunique() + 1 if fecha not in df["Fecha"].dropna().values else df[df["Fecha"] == fecha]["N"].iloc[0]

        depositos = st.session_state.df.copy()
        monto_deposito = depositos[
            (depositos["Fecha"] == fecha) & (depositos["Empresa"] == proveedor)
        ]["Monto"].sum()
        saldo_diario = monto_deposito - total
        saldo_acumulado = df["Saldo Acumulado"].dropna().iloc[-1] + saldo_diario if df["Saldo Acumulado"].dropna().shape[0] > 0 else - 243.30 + saldo_diario

        nueva_fila = {
            "N": enumeracion,
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
            "Monto Deposito": monto_deposito,
            "Saldo diario": saldo_diario,
            "Saldo Acumulado": saldo_acumulado
        }

        st.session_state.data = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
        st.success("Registro agregado correctamente")
        st.session_state.data.to_pickle(DATA_FILE)

    # Registro de Nota de Debito
    st.subheader("Registro de Nota de Debito")
    with st.form("nota_debito"):
        col1, col2, col3 = st.columns(3)
        with col1:
            fecha_nota = st.date_input("Fecha de Nota")
        with col2:
            descuento = st.number_input("Descuento (%)", min_value=0.0, max_value=1.0, step=0.01)
        with col3:
            descuento_real = st.number_input("Descuento Real ($)", min_value=0.0, step=0.01)
        agregar_nota = st.form_submit_button("Agregar Nota de Debito")

    if agregar_nota:
        df = st.session_state.data.copy()
        libras_calculadas = df[df["Fecha"] == fecha_nota]["Libras Restantes"].sum()
        descuento_posible = libras_calculadas * descuento
        nueva_nota = {
            "Fecha": fecha_nota,
            "Libras calculadas": libras_calculadas,
            "Descuento": descuento,
            "Descuento posible": descuento_posible,
            "Descuento real": descuento_real
        }
        st.session_state.notas = pd.concat([st.session_state.notas, pd.DataFrame([nueva_nota])], ignore_index=True)
        st.session_state.notas.to_pickle(DEBIT_NOTES_FILE)
        st.success("Nota de debito agregada correctamente")

    # Actualizar saldo acumulado con descuento real
    for i, nota in st.session_state.notas.iterrows():
        fecha = nota["Fecha"]
        descuento_real = nota["Descuento real"]
        indices = st.session_state.data[st.session_state.data["Fecha"] >= fecha].index
        for j in indices:
            if pd.notna(descuento_real):
                st.session_state.data.at[j, "Saldo Acumulado"] += descuento_real

    # Mostrar tabla
    st.subheader("Tabla de Registros")
    st.session_state.data["Mostrar"] = st.session_state.data.apply(
        lambda row: f"{row['Fecha']} - {row['Proveedor']} - ${row['Total ($)']:.2f}"
        if pd.notna(row["Total ($)"]) else f"{row['Fecha']} - {row['Proveedor']} - Sin total",
        axis=1
    )
    registro_a_eliminar = st.selectbox("Selecciona un registro para eliminar", st.session_state.data["Mostrar"])
    if st.button("Eliminar Registro Seleccionado"):
        index_eliminar = st.session_state.data[st.session_state.data["Mostrar"] == registro_a_eliminar].index[0]
        st.session_state.data.drop(index=index_eliminar, inplace=True)
        st.session_state.data.reset_index(drop=True, inplace=True)
        st.session_state.data.to_pickle(DATA_FILE)
        st.success("Registro eliminado correctamente")

    df_display = st.session_state.data.copy()
    df_display["Saldo diario"] = df_display["Saldo diario"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
    df_display["Saldo Acumulado"] = df_display["Saldo Acumulado"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
    st.dataframe(df_display.drop(columns=["Mostrar"], errors="ignore"), use_container_width=True)

    # Tabla de Notas de Debito
    st.subheader("Tabla de Notas de Debito")
    st.dataframe(st.session_state.notas.drop(columns=["Mostrar"], errors="ignore"), use_container_width=True)

    # Eliminar Nota de Debito
    st.subheader("Eliminar una Nota de Debito")
    if not st.session_state.notas.empty:
        st.session_state.notas["Mostrar"] = st.session_state.notas.apply(
            lambda row: f"{row['Fecha']} - Libras: {row['Libras calculadas']:.2f} - Descuento real: ${row['Descuento real']:.2f}", axis=1
        )
        nota_a_eliminar = st.selectbox("Selecciona una nota para eliminar", st.session_state.notas["Mostrar"])
        if st.button("Eliminar Nota de Debito seleccionada"):
            index_eliminar = st.session_state.notas[st.session_state.notas["Mostrar"] == nota_a_eliminar].index[0]
            st.session_state.notas.drop(index=index_eliminar, inplace=True)
            st.session_state.notas.reset_index(drop=True, inplace=True)
            st.session_state.notas.to_pickle(DEBIT_NOTES_FILE)
            st.success("Nota de debito eliminada correctamente.")

    @st.cache_data
    def convertir_excel(df):
        output = BytesIO()
        df_copy = df.copy()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_copy.to_excel(writer, index=False)
        output.seek(0)
        return output

    st.download_button(
        label="Descargar Registros Excel",
        data=convertir_excel(st.session_state.data.drop(columns=["Mostrar"], errors="ignore")),
        file_name="registro_proveedores_depositos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    with st.expander("Ver depositos registrados"):
        st.dataframe(st.session_state.df.drop(columns=["Mostrar"], errors="ignore"), use_container_width=True)

elif opcion == "Reporte Semanal":
    st.header("Reporte Semanal")
    df = st.session_state.data.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    semana_actual = df["Fecha"].dt.isocalendar().week.max()
    df_semana = df[df["Fecha"].dt.isocalendar().week == semana_actual]
    st.dataframe(df_semana.drop(columns=["Mostrar"], errors="ignore"), use_container_width=True)

elif opcion == "Reporte Mensual":
    st.header("Reporte Mensual")
    df = st.session_state.data.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    mes_actual = datetime.today().month
    df_mes = df[df["Fecha"].dt.month == mes_actual]
    st.dataframe(df_mes.drop(columns=["Mostrar"], errors="ignore"), use_container_width=True)

elif opcion == "Graficos":
    st.header("Graficos de Proveedores")
    df = st.session_state.data.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    total_por_proveedor = df.groupby("Proveedor")["Total ($)"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots()
    total_por_proveedor.plot(kind="bar", ax=ax)
    ax.set_ylabel("Total ($)")
    ax.set_title("Total por Proveedor")
    st.pyplot(fig)

    st.subheader("Saldo Acumulado a lo largo del tiempo")
    df_ordenado = df.sort_values("Fecha")
    fig2, ax2 = plt.subplots()
    ax2.plot(df_ordenado["Fecha"], df_ordenado["Saldo Acumulado"], marker="o")
    ax2.set_ylabel("Saldo Acumulado ($)")
    ax2.set_title("Evalucion del Saldo Acumulado")
    st.pyplot(fig2)
