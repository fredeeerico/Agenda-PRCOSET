import streamlit as st
import psycopg2
from datetime import date, time, datetime, timedelta, timezone
import pandas as pd
from io import BytesIO

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

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
# BOTÃO PARA GERAR EVENTOS DE TESTE (UMA VEZ)
# -----------------------------
if st.sidebar.button("🚀 Gerar 10 eventos de teste"):
    hoje = datetime.now().date()
    ontem = hoje - timedelta(days=1)
    semana_passada = hoje - timedelta(days=7)
    amanha = hoje + timedelta(days=1)
    proxima_semana = hoje + timedelta(days=7)

    eventos_teste = [
        (1,"Reunião Estratégica", ontem, "09:00","10:00","Prefeitura","Sala 1","Redes, Foto","Fred","Câmera","Obs",0,"","", "ATIVO"),
        (0,"Visita Técnica", ontem, "14:00","15:00","Obra Central","Endereço X","Vídeo","Ana","Drone","Obs",1,"Carlos","11999999999","ATIVO"),
        (1,"Coletiva de Imprensa", semana_passada, "10:00","11:00","Auditório","Centro","Imprensa","Thais","Microfone","Obs",0,"","", "CANCELADO"),
        (0,"Evento Comunitário", semana_passada, "16:00","18:00","Praça","Bairro Y","Foto","Fred, Ana","Câmera","Obs",0,"","", "ATIVO"),
        (1,"Reunião com Secretários", hoje, "08:00","09:30","Gabinete","Prefeitura","Redes","Fred, Thais","Notebook","Obs",1,"João","11988888888","ATIVO"),
        (0,"Entrega de Obras", hoje, "11:00","12:00","Obra Z","Endereço Z","Vídeo, Foto","Ana","Drone","Obs",0,"","", "ATIVO"),
        (1,"Agenda Oficial", amanha, "09:00","10:00","Gabinete","Prefeitura","Redes","Fred","Câmera","Obs",0,"","", "ATIVO"),
        (0,"Reunião Planejamento", amanha, "15:00","16:00","Sala 3","Prefeitura","Foto","Thais","Tripé","Obs",0,"","", "ATIVO"),
        (1,"Evento Regional", proxima_semana, "10:00","12:00","Centro Eventos","Centro","Imprensa","Fred, Ana, Thais","Kit completo","Obs",1,"Marcos","11977777777","ATIVO"),
        (0,"Visita Escolar", proxima_semana, "14:00","15:30","Escola ABC","Bairro W","Foto","Ana","Câmera","Obs",0,"","", "ATIVO"),
    ]

    for ev in eventos_teste:
        cursor.execute("""
        INSERT INTO eventos (
            agenda_presidente, titulo, data, hora_inicio, hora_fim,
            local, endereco, cobertura, responsaveis, equipamentos,
            observacoes, precisa_motorista, motorista_nome, motorista_telefone, status
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            ev[0], ev[1], ev[2].isoformat(), ev[3], ev[4],
            ev[5], ev[6], ev[7], ev[8], ev[9],
            ev[10], ev[11], ev[12], ev[13], ev[14]
        ))

    conn.commit()
    st.success("✅ Eventos de teste criados!")

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
