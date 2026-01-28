import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime, timedelta, timezone
import pandas as pd

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO

# -----------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------
st.set_page_config(
    page_title="Agenda PRCOSET",
    page_icon="📅",
    layout="centered"
)

st.title("📅 Agenda PRCOSET")

# -----------------------------
# CONEXÃO SUPABASE
# -----------------------------
conn = psycopg2.connect(
    host=st.secrets["DB_HOST"],
    database=st.secrets["DB_NAME"],
    user=st.secrets["DB_USER"],
    password=st.secrets["DB_PASSWORD"],
    port=st.secrets["DB_PORT"],
    sslmode=st.secrets["DB_SSLMODE"],
    cursor_factory=RealDictCursor
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS eventos (
    id SERIAL PRIMARY KEY,
    agenda_presidente BOOLEAN,
    titulo TEXT,
    data DATE,
    hora_inicio TIME,
    hora_fim TIME,
    local TEXT,
    endereco TEXT,
    cobertura TEXT,
    responsaveis TEXT,
    equipamentos TEXT,
    observacoes TEXT,
    precisa_motorista BOOLEAN,
    motorista_nome TEXT,
    motorista_telefone TEXT,
    status TEXT
)
""")
conn.commit()

# -----------------------------
# ESTADO GLOBAL
# -----------------------------
if "editando" not in st.session_state:
    st.session_state.editando = False

if "evento_id" not in st.session_state:
    st.session_state.evento_id = None

# -----------------------------
# FUNÇÃO PDF
# -----------------------------
def gerar_pdf_eventos(eventos_lista):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Agenda PRCOSET - Eventos", styles["Title"]))
    elementos.append(Spacer(1, 12))

    for ev in eventos_lista:
        texto = f"""
        <b>{ev['titulo']}</b><br/>
        📅 {ev['data']} | ⏰ {ev['hora_inicio']} às {ev['hora_fim']}<br/>
        📍 {ev['local']}<br/>
        🏠 {ev['endereco']}<br/>
        🎥 {ev['cobertura']}<br/>
        👥 {ev['responsaveis']}<br/>
        🎒 {ev['equipamentos']}<br/>
        🚗 {ev['motorista_nome'] or ""} {ev['motorista_telefone'] or ""}<br/>
        📝 {ev['observacoes']}<br/>
        Status: {ev['status']}<br/><br/>
        """
        elementos.append(Paragraph(texto, styles["Normal"]))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

# -----------------------------
# ABAS
# -----------------------------
aba_eventos, aba_form = st.tabs(["📋 Eventos", "📝 Novo Evento"])

# =====================================================
# 📝 NOVO EVENTO
# =====================================================
with aba_form:

    evento = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        evento = cursor.fetchone()
        st.warning("✏️ Editando evento existente")

    with st.form("form_evento"):
        agenda_presidente = st.checkbox("👑 Agenda do Presidente?", value=evento["agenda_presidente"] if evento else False)
        precisa_motorista = st.checkbox("🚗 Precisa de motorista?", value=evento["precisa_motorista"] if evento else False)

        titulo = st.text_input("📝 Título", value=evento["titulo"] if evento else "")

        col1, col2, col3 = st.columns(3)
        with col1:
            data_evento = st.date_input("📅 Data", value=evento["data"] if evento else date.today())
        with col2:
            hora_inicio = st.time_input("⏰ Início", value=evento["hora_inicio"] if evento else datetime.now().time())
        with col3:
            hora_fim = st.time_input("⏰ Fim", value=evento["hora_fim"] if evento else datetime.now().time())

        local = st.text_input("📍 Local", value=evento["local"] if evento else "")
        endereco = st.text_input("🏠 Endereço", value=evento["endereco"] if evento else "")
        cobertura = st.text_input("🎥 Cobertura", value=evento["cobertura"] if evento else "")
        responsaveis = st.text_input("👥 Responsáveis", value=evento["responsaveis"] if evento else "")
        equipamentos = st.text_input("🎒 Equipamentos", value=evento["equipamentos"] if evento else "")
        observacoes = st.text_area("📝 Observações", value=evento["observacoes"] if evento else "")

        motorista_nome = st.text_input("Motorista", value=evento["motorista_nome"] if evento else "") if precisa_motorista else ""
        motorista_telefone = st.text_input("Telefone motorista", value=evento["motorista_telefone"] if evento else "") if precisa_motorista else ""

        status = st.selectbox("Status", ["ATIVO", "CANCELADO"], index=0 if not evento or evento["status"]=="ATIVO" else 1)

        if st.form_submit_button("💾 Salvar"):
            dados = (
                agenda_presidente, titulo, data_evento,
                hora_inicio, hora_fim,
                local, endereco, cobertura,
                responsaveis, equipamentos, observacoes,
                precisa_motorista, motorista_nome,
                motorista_telefone, status
            )

            if evento:
                cursor.execute("""
                UPDATE eventos SET
                agenda_presidente=%s, titulo=%s, data=%s, hora_inicio=%s, hora_fim=%s,
                local=%s, endereco=%s, cobertura=%s, responsaveis=%s, equipamentos=%s,
                observacoes=%s, precisa_motorista=%s, motorista_nome=%s,
                motorista_telefone=%s, status=%s
                WHERE id=%s
                """, dados + (st.session_state.evento_id,))
            else:
                cursor.execute("""
                INSERT INTO eventos (
                agenda_presidente,titulo,data,hora_inicio,hora_fim,
                local,endereco,cobertura,responsaveis,equipamentos,
                observacoes,precisa_motorista,motorista_nome,motorista_telefone,status
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, dados)

            conn.commit()
            st.session_state.editando = False
            st.session_state.evento_id = None
            st.rerun()

# =====================================================
# 📋 EVENTOS
# =====================================================
with aba_eventos:

    cursor.execute("SELECT * FROM eventos ORDER BY data, hora_inicio")
    eventos = cursor.fetchall()

    for ev in eventos:
        st.markdown(f"""
        ### {ev['titulo']}
        📅 {ev['data']} ⏰ {ev['hora_inicio']} às {ev['hora_fim']}  
        📍 {ev['local']}  
        👥 {ev['responsaveis']}  
        **Status:** {ev['status']}
        """)

        c1, c2, c3 = st.columns(3)

        if c1.button("✏️ Editar", key=f"e{ev['id']}"):
            st.session_state.editando = True
            st.session_state.evento_id = ev["id"]
            st.rerun()

        if c2.button("❌ Cancelar/Reativar", key=f"c{ev['id']}"):
            novo = "CANCELADO" if ev["status"]=="ATIVO" else "ATIVO"
            cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", (novo, ev["id"]))
            conn.commit()
            st.rerun()

        if c3.button("🗑 Apagar", key=f"d{ev['id']}"):
            cursor.execute("DELETE FROM eventos WHERE id=%s", (ev["id"],))
            conn.commit()
            st.rerun()
