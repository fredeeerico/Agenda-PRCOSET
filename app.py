import streamlit as st
import psycopg2
from datetime import date, time, datetime, timedelta, timezone
import pandas as pd

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO

# -----------------------------
# CONEXÃO POSTGRES (SUPABASE)
# -----------------------------
conn = psycopg2.connect(
    host=st.secrets["DB_HOST"],
    database=st.secrets["DB_NAME"],
    user=st.secrets["DB_USER"],
    password=st.secrets["DB_PASSWORD"],
    port=st.secrets["DB_PORT"],
    sslmode=st.secrets["DB_SSLMODE"],
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS eventos (
    id SERIAL PRIMARY KEY,
    agenda_presidente INTEGER,
    titulo TEXT,
    data TEXT,
    hora_inicio TEXT,
    hora_fim TEXT,
    local TEXT,
    endereco TEXT,
    cobertura TEXT,
    responsaveis TEXT,
    equipamentos TEXT,
    observacoes TEXT,
    precisa_motorista INTEGER,
    motorista_nome TEXT,
    motorista_telefone TEXT,
    status TEXT
)
""")
conn.commit()

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
# ESTADO GLOBAL
# -----------------------------
if "editando" not in st.session_state:
    st.session_state.editando = False

if "evento_id" not in st.session_state:
    st.session_state.evento_id = None

# -----------------------------
# ABAS
# -----------------------------
aba_eventos, aba_form = st.tabs(["📋 Eventos", "📝 Novo Evento"])

# =====================================================
# 📝 ABA NOVO EVENTO
# =====================================================
with aba_form:
    evento = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("""
        SELECT id, agenda_presidente, titulo, data, hora_inicio, hora_fim,
        local, endereco, cobertura, responsaveis, equipamentos,
        observacoes, precisa_motorista, motorista_nome,
        motorista_telefone, status
        FROM eventos WHERE id=%s
        """, (st.session_state.evento_id,))
        evento = cursor.fetchone()
        st.warning("✏️ Você está editando um evento já existente.")

    with st.form("form_evento"):
        agenda_presidente = st.checkbox("👑 Agenda do Presidente?", value=bool(evento[1]) if evento else False)
        precisa_motorista = st.checkbox("🚗 Precisa de motorista?", value=bool(evento[12]) if evento else False)
        titulo = st.text_input("📝 Título", value=evento[2] if evento else "")

        col1, col2, col3 = st.columns(3)
        with col1:
            data_evento = st.date_input("📅 Data", value=date.fromisoformat(evento[3]) if evento else date.today())
        with col2:
            hora_inicio = st.time_input("⏰ Início", value=time.fromisoformat(evento[4]) if evento else time(9,0))
        with col3:
            hora_fim = st.time_input("⏰ Fim", value=time.fromisoformat(evento[5]) if evento else time(10,0))

        local = st.text_input("📍 Local", value=evento[6] if evento else "")
        endereco = st.text_input("🏠 Endereço", value=evento[7] if evento else "")
        cobertura = st.multiselect("🎥 Cobertura", ["Redes", "Foto", "Vídeo", "Imprensa"],
                                   default=evento[8].split(", ") if evento and evento[8] else [])
        responsaveis = st.text_input("👥 Responsáveis", value=evento[9] if evento else "")
        equipamentos = st.text_input("🎒 Equipamentos", value=evento[10] if evento else "")
        observacoes = st.text_area("📝 Observações", value=evento[11] if evento else "")

        motorista_nome = ""
        motorista_telefone = ""
        if precisa_motorista:
            motorista_nome = st.text_input("Nome do motorista", value=evento[13] if evento else "")
            motorista_telefone = st.text_input("Telefone do motorista", value=evento[14] if evento else "")

        status = st.selectbox("Status", ["ATIVO", "CANCELADO"],
                              index=0 if not evento or evento[15]=="ATIVO" else 1)

        if st.form_submit_button("💾 Salvar"):
            dados = (
                1 if agenda_presidente else 0,
                titulo, data_evento.isoformat(),
                hora_inicio.strftime("%H:%M"), hora_fim.strftime("%H:%M"),
                local, endereco, ", ".join(cobertura),
                responsaveis, equipamentos, observacoes,
                1 if precisa_motorista else 0,
                motorista_nome, motorista_telefone, status
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
# 📋 ABA EVENTOS
# =====================================================
with aba_eventos:
    col_filtro, col_lista = st.columns([1,3])

    with col_filtro:
        st.subheader("🔍 Filtros")
        filtro_data = st.date_input("📅 Data", value=None)
        filtro_agenda = st.selectbox("📂 Agenda", ["Todas","Agenda do Presidente","Outras agendas"])
        filtro_responsavel = st.text_input("👥 Responsável")

    cursor.execute("""
    SELECT id, agenda_presidente, titulo, data, hora_inicio, hora_fim,
    local, endereco, cobertura, responsaveis, equipamentos,
    observacoes, precisa_motorista, motorista_nome,
    motorista_telefone, status
    FROM eventos
    ORDER BY data ASC, hora_inicio ASC, hora_fim ASC, agenda_presidente DESC
    """)
    eventos = cursor.fetchall()

    hoje = date.today()
    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)

    eventos_visiveis = []

    for ev in eventos:
        data_db = datetime.strptime(ev[3], "%Y-%m-%d").date()

        if filtro_data is not None and filtro_data != "" and data_db != filtro_data:
            continue
        if filtro_agenda == "Agenda do Presidente" and not ev[1]:
            continue
        if filtro_agenda == "Outras agendas" and ev[1]:
            continue
        if filtro_responsavel and filtro_responsavel.lower() not in (ev[9] or "").lower():
            continue

        eventos_visiveis.append(ev)

    # (o restante do seu código de renderização dos cards permanece IGUAL)
