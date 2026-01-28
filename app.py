import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅")
st.title("📅 Agenda PRCOSET")

# ------------------ CONEXÃO ------------------
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

# ------------------ SESSION ------------------
if "editando" not in st.session_state:
    st.session_state.editando = False
if "evento_id" not in st.session_state:
    st.session_state.evento_id = None

# ------------------ ABAS ------------------
aba_eventos, aba_form = st.tabs(["📋 Eventos", "📝 Novo Evento"])

# ================= FORM =================
with aba_form:
    evento = None
    if st.session_state.editando:
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        evento = cursor.fetchone()

    with st.form("form"):
        agenda_presidente = st.checkbox("Agenda do Presidente", value=evento["agenda_presidente"] if evento else False)
        precisa_motorista = st.checkbox("Precisa de motorista", value=evento["precisa_motorista"] if evento else False)

        titulo = st.text_input("Título", value=evento["titulo"] if evento else "")
        data_evento = st.date_input("Data", value=evento["data"] if evento else date.today())
        hora_inicio = st.time_input("Início", value=evento["hora_inicio"] if evento else datetime.now().time())
        hora_fim = st.time_input("Fim", value=evento["hora_fim"] if evento else datetime.now().time())

        local = st.text_input("Local", value=evento["local"] if evento else "")
        endereco = st.text_input("Endereço", value=evento["endereco"] if evento else "")
        cobertura = st.text_input("Cobertura", value=evento["cobertura"] if evento else "")
        responsaveis = st.text_input("Responsáveis", value=evento["responsaveis"] if evento else "")
        equipamentos = st.text_input("Equipamentos", value=evento["equipamentos"] if evento else "")
        observacoes = st.text_area("Observações", value=evento["observacoes"] if evento else "")

        motorista_nome = st.text_input("Motorista", value=evento["motorista_nome"] if evento else "") if precisa_motorista else ""
        motorista_telefone = st.text_input("Telefone", value=evento["motorista_telefone"] if evento else "") if precisa_motorista else ""

        status = st.selectbox("Status", ["ATIVO", "CANCELADO"], index=0 if not evento or evento["status"]=="ATIVO" else 1)

        if st.form_submit_button("Salvar"):
            dados = (
                bool(agenda_presidente),
                titulo,
                data_evento,
                hora_inicio,
                hora_fim,
                local,
                endereco,
                cobertura,
                responsaveis,
                equipamentos,
                observacoes,
                bool(precisa_motorista),
                motorista_nome,
                motorista_telefone,
                status
            )

            if evento:
                cursor.execute("""
                UPDATE eventos SET
                agenda_presidente=%s, titulo=%s, data=%s, hora_inicio=%s, hora_fim=%s,
                local=%s, endereco=%s, cobertura=%s, responsaveis=%s,
                equipamentos=%s, observacoes=%s, precisa_motorista=%s,
                motorista_nome=%s, motorista_telefone=%s, status=%s
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
            st.rerun()

# ================= LISTA + FILTROS =================
with aba_eventos:
    st.subheader("Filtros")
    filtro_data = st.date_input("Data", value=None)
    filtro_responsavel = st.text_input("Responsável")

    cursor.execute("SELECT * FROM eventos ORDER BY data, hora_inicio")
    eventos = cursor.fetchall()

    for ev in eventos:
        if filtro_data and ev["data"] != filtro_data:
            continue
        if filtro_responsavel and filtro_responsavel.lower() not in (ev["responsaveis"] or "").lower():
            continue

        st.markdown(f"""
        ### {ev['titulo']}
        📅 {ev['data']} ⏰ {ev['hora_inicio']} às {ev['hora_fim']}  
        📍 {ev['local']}  
        👥 {ev['responsaveis']}  
        **Status:** {ev['status']}
        """)

        c1, c2, c3 = st.columns(3)

        if c1.button("Editar", key=f"e{ev['id']}"):
            st.session_state.editando = True
            st.session_state.evento_id = ev["id"]
            st.rerun()

        if c2.button("Cancelar/Reativar", key=f"c{ev['id']}"):
            novo = "CANCELADO" if ev["status"]=="ATIVO" else "ATIVO"
            cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", (novo, ev["id"]))
            conn.commit()
            st.rerun()

        if c3.button("Apagar", key=f"d{ev['id']}"):
            cursor.execute("DELETE FROM eventos WHERE id=%s", (ev["id"],))
            conn.commit()
            st.rerun()
