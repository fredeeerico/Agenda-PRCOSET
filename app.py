import streamlit as st
import psycopg2
from datetime import date, time, datetime, timedelta, timezone

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

# -----------------------------
# CRIA TABELA
# -----------------------------
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
# INSERE EVENTOS TESTE (SÓ 1 VEZ)
# -----------------------------
cursor.execute("SELECT COUNT(*) FROM eventos;")
if cursor.fetchone()[0] == 0:

    hoje = datetime.now().date()
    eventos = [
        (1,"Reunião Estratégica", hoje - timedelta(days=1), "09:00","10:00","Prefeitura","Sala 1","Redes, Foto","Fred","Câmera","Obs",0,"","", "ATIVO"),
        (0,"Visita Técnica", hoje - timedelta(days=7), "14:00","15:00","Obra Central","End X","Vídeo","Ana","Drone","Obs",1,"Carlos","11999999999","ATIVO"),
        (1,"Reunião Secretários", hoje, "08:00","09:30","Gabinete","Prefeitura","Redes","Fred, Thais","Notebook","Obs",1,"João","11988888888","ATIVO"),
        (0,"Entrega Obras", hoje, "11:00","12:00","Obra Z","End Z","Vídeo, Foto","Ana","Drone","Obs",0,"","", "ATIVO"),
        (1,"Agenda Oficial", hoje + timedelta(days=1), "09:00","10:00","Gabinete","Prefeitura","Redes","Fred","Câmera","Obs",0,"","", "ATIVO"),
        (0,"Planejamento", hoje + timedelta(days=1), "15:00","16:00","Sala 3","Prefeitura","Foto","Thais","Tripé","Obs",0,"","", "ATIVO"),
        (1,"Evento Regional", hoje + timedelta(days=7), "10:00","12:00","Centro","Centro","Imprensa","Fred, Ana, Thais","Kit","Obs",1,"Marcos","11977777777","ATIVO"),
        (0,"Visita Escolar", hoje + timedelta(days=7), "14:00","15:30","Escola","Bairro","Foto","Ana","Câmera","Obs",0,"","", "ATIVO"),
        (1,"Coletiva Imprensa", hoje - timedelta(days=7), "10:00","11:00","Auditório","Centro","Imprensa","Thais","Mic","Obs",0,"","", "CANCELADO"),
        (0,"Evento Comunidade", hoje - timedelta(days=7), "16:00","18:00","Praça","Bairro","Foto","Fred, Ana","Câmera","Obs",0,"","", "ATIVO"),
    ]

    for e in eventos:
        cursor.execute("""
        INSERT INTO eventos (
            agenda_presidente,titulo,data,hora_inicio,hora_fim,
            local,endereco,cobertura,responsaveis,equipamentos,
            observacoes,precisa_motorista,motorista_nome,motorista_telefone,status
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            e[0], e[1], e[2].isoformat(), e[3], e[4],
            e[5], e[6], e[7], e[8], e[9],
            e[10], e[11], e[12], e[13], e[14]
        ))

    conn.commit()

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅")
st.title("📅 Agenda PRCOSET")

aba_eventos, aba_form = st.tabs(["📋 Eventos", "📝 Novo Evento"])

# -----------------------------
# FORM
# -----------------------------
with aba_form:
    with st.form("novo"):
        titulo = st.text_input("Título")
        data_evento = st.date_input("Data")
        hora_inicio = st.time_input("Início")
        hora_fim = st.time_input("Fim")
        responsaveis = st.text_input("Responsáveis")
        agenda_presidente = st.checkbox("Agenda do Presidente")

        if st.form_submit_button("Salvar"):
            cursor.execute("""
            INSERT INTO eventos (
                agenda_presidente,titulo,data,hora_inicio,hora_fim,
                local,endereco,cobertura,responsaveis,equipamentos,
                observacoes,precisa_motorista,motorista_nome,motorista_telefone,status
            ) VALUES (%s,%s,%s,%s,%s,'','','',%s,'','','', '', 'ATIVO')
            """, (
                1 if agenda_presidente else 0,
                titulo,
                data_evento.isoformat(),
                hora_inicio.strftime("%H:%M"),
                hora_fim.strftime("%H:%M"),
                responsaveis
            ))
            conn.commit()
            st.success("Salvo!")

# -----------------------------
# LISTA + FILTROS
# -----------------------------
with aba_eventos:
    filtro_data = st.date_input("Filtrar por data", value=None)
    filtro_resp = st.text_input("Filtrar por responsável")

    cursor.execute("SELECT * FROM eventos ORDER BY data, hora_inicio")
    eventos = cursor.fetchall()

    for ev in eventos:
        data_db = datetime.strptime(ev[3], "%Y-%m-%d").date()

        if filtro_data and data_db != filtro_data:
            continue
        if filtro_resp and filtro_resp.lower() not in (ev[9] or "").lower():
            continue

        st.markdown(f"""
        ---
        ### {ev[2]}
        📅 {ev[3]} ⏰ {ev[4]} às {ev[5]}  
        👥 {ev[9]}  
        Status: {ev[15]}
        """)
