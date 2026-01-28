# app.py - Agenda PRCOSET
# 🚨 Requisitos: streamlit, psycopg2, reportlab, pandas, supabase já configurado

import streamlit as st
import psycopg2
from datetime import date, time, datetime, timedelta, timezone
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# -----------------------------
# CORES E ESTILOS - EDITÁVEL
# -----------------------------
CORES = {
    "fundo_presidente": "#2b488e",
    "fundo_outras": "#109439",
    "fundo_passado": "#d9d9d9",
    "texto_presidente": "#ffffff",
    "texto_outras": "#0f1116",
    "texto_passado": "#6b6b6b",
    "borda_amarela": "#FFD700",
    "borda_vermelha": "#ff2b2b",
    "badge_hoje_bg": "#FFD700",
    "badge_hoje_text": "#000000",
    "badge_agora_bg": "#ff2b2b",
    "badge_agora_text": "#ffffff",
}

# -----------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------
st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅", layout="centered")
st.title("📅 Agenda PRCOSET")

# -----------------------------
# ESTADO GLOBAL
# -----------------------------
if "editando" not in st.session_state: st.session_state.editando = False
if "evento_id" not in st.session_state: st.session_state.evento_id = None

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
# INSERÇÃO DE 10 EVENTOS DE TESTE
# -----------------------------
cursor.execute("SELECT COUNT(*) FROM eventos")
if cursor.fetchone()[0]==0:
    hoje = datetime.now(timezone(timedelta(hours=-3))).date()
    ontem = hoje - timedelta(days=1)
    semana_passada = hoje - timedelta(days=7)
    amanha = hoje + timedelta(days=1)
    proxima_semana = hoje + timedelta(days=7)

    eventos_teste = [
        # Ontem
        (True,"Reunião Estratégica", ontem,"09:00","10:00","Prefeitura","Sala 1","Redes, Foto","Fred","Câmera","Obs",False,"","", "ATIVO"),
        (False,"Visita Técnica", ontem,"14:00","15:00","Obra Central","Endereço X","Vídeo","Ana","Drone","Obs",True,"Carlos","11999999999","ATIVO"),

        # Semana passada
        (True,"Coletiva de Imprensa", semana_passada,"10:00","11:00","Auditório","Centro","Imprensa","Thais","Microfone","Obs",False,"","", "CANCELADO"),
        (False,"Evento Comunitário", semana_passada,"16:00","18:00","Praça","Bairro Y","Foto","Fred, Ana","Câmera","Obs",False,"","", "ATIVO"),

        # Hoje
        (True,"Reunião com Secretários", hoje,"08:00","09:30","Gabinete","Prefeitura","Redes","Fred, Thais","Notebook","Obs",True,"João","11988888888","ATIVO"),
        (False,"Entrega de Obras", hoje,"11:00","12:00","Obra Z","Endereço Z","Vídeo, Foto","Ana","Drone","Obs",False,"","", "ATIVO"),

        # Amanhã
        (True,"Agenda Oficial", amanha,"09:00","10:00","Gabinete","Prefeitura","Redes","Fred","Câmera","Obs",False,"","", "ATIVO"),
        (False,"Reunião Planejamento", amanha,"15:00","16:00","Sala 3","Prefeitura","Foto","Thais","Tripé","Obs",False,"","", "ATIVO"),

        # Próxima semana
        (True,"Evento Regional", proxima_semana,"10:00","12:00","Centro Eventos","Centro","Imprensa","Fred, Ana, Thais","Kit completo","Obs",True,"Marcos","11977777777","ATIVO"),
        (False,"Visita Escolar", proxima_semana,"14:00","15:30","Escola ABC","Bairro W","Foto","Ana","Câmera","Obs",False,"","", "ATIVO"),
    ]

    for ev in eventos_teste:
        cursor.execute("""
        INSERT INTO eventos (agenda_presidente,titulo,data,hora_inicio,hora_fim,local,endereco,cobertura,
            responsaveis,equipamentos,observacoes,precisa_motorista,motorista_nome,motorista_telefone,status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            ev[0], ev[1], ev[2], ev[3], ev[4], ev[5], ev[6], ev[7],
            ev[8], ev[9], ev[10], ev[11], ev[12], ev[13], ev[14]
        ))
    conn.commit()

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
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        evento = cursor.fetchone()
        st.warning("✏️ Você está editando um evento já existente.")

    with st.form("form_evento"):
        agenda_presidente = st.checkbox("👑 Agenda do Presidente?", value=bool(evento[1]) if evento else False)
        precisa_motorista = st.checkbox("🚗 Precisa de motorista?", value=bool(evento[12]) if evento else False)
        titulo = st.text_input("📝 Título", value=evento[2] if evento else "")

        col1, col2, col3 = st.columns(3)
        with col1: data_evento = st.date_input("📅 Data", value=evento[3] if evento else date.today())
        with col2: hora_inicio = st.time_input("⏰ Início", value=evento[4] if evento else time(9,0))
        with col3: hora_fim = st.time_input("⏰ Fim", value=evento[5] if evento else time(10,0))

        local = st.text_input("📍 Local", value=evento[6] if evento else "")
        endereco = st.text_input("🏠 Endereço", value=evento[7] if evento else "")
        cobertura = st.multiselect("🎥 Cobertura", ["Redes","Foto","Vídeo","Imprensa"],
                                   default=evento[8].split(", ") if evento and evento[8] else [])
        responsaveis = st.text_input("👥 Responsáveis", value=evento[9] if evento else "")
        equipamentos = st.text_input("🎒 Equipamentos", value=evento[10] if evento else "")
        observacoes = st.text_area("📝 Observações", value=evento[11] if evento else "")

        motorista_nome = st.text_input("Nome do motorista", value=evento[13] if evento and precisa_motorista else "")
        motorista_telefone = st.text_input("Telefone do motorista", value=evento[14] if evento and precisa_motorista else "")
        status = st.selectbox("Status", ["ATIVO","CANCELADO"], index=0 if not evento or evento[15]=="ATIVO" else 1)

        if st.form_submit_button("💾 Salvar"):
            dados = (
                agenda_presidente, titulo, data_evento, hora_inicio, hora_fim,
                local, endereco, ", ".join(cobertura), responsaveis,
                equipamentos, observacoes, precisa_motorista, motorista_nome,
                motorista_telefone, status
            )
            if evento:
                cursor.execute("""
                    UPDATE eventos SET agenda_presidente=%s, titulo=%s, data=%s, hora_inicio=%s, hora_fim=%s,
                    local=%s, endereco=%s, cobertura=%s, responsaveis=%s, equipamentos=%s, observacoes=%s,
                    precisa_motorista=%s, motorista_nome=%s, motorista_telefone=%s, status=%s
                    WHERE id=%s
                """, dados + (st.session_state.evento_id,))
            else:
                cursor.execute("""
                    INSERT INTO eventos (agenda_presidente,titulo,data,hora_inicio,hora_fim,local,endereco,cobertura,
                    responsaveis,equipamentos,observacoes,precisa_motorista,motorista_nome,motorista_telefone,status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, dados)
            conn.commit()
            st.session_state.editando = False
            st.session_state.evento_id = None
            st.experimental_rerun()

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

    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC")
    eventos = cursor.fetchall()
    agora = datetime.now(timezone(timedelta(hours=-3)))

    # Renderização de cards
    for ev in eventos:
        eid, agenda_pres, titulo, data_ev, hi, hf, local, endereco, cobertura, resp, equip, obs, precisa_motor, nome_motor, tel_motor, status = ev
        data_dt = data_ev if isinstance(data_ev,date) else datetime.strptime(str(data_ev), "%Y-%m-%d").date()
        hi_dt = datetime.strptime(str(hi)[:5],"%H:%M").time()
        hf_dt = datetime.strptime(str(hf)[:5],"%H:%M").time()
        inicio_dt = datetime.combine(data_dt, hi_dt)
        fim_dt = datetime.combine(data_dt, hf_dt)

        # Filtros
        if filtro_data and data_dt != filtro_data: continue
        if filtro_agenda=="Agenda do Presidente" and not agenda_pres: continue
        if filtro_agenda=="Outras agendas" and agenda_pres: continue
        if filtro_responsavel and filtro_responsavel.lower() not in (resp or "").lower(): continue

        # Cores e badge
        cor_fundo = CORES["fundo_presidente"] if agenda_pres else CORES["fundo_outras"]
        cor_fonte = CORES["texto_presidente"] if agenda_pres else CORES["texto_outras"]
        borda = "none"
        badge = ""

        if data_dt < agora.date() or (data_dt==agora.date() and agora>fim_dt):
            cor_fundo = CORES["fundo_passado"]
            cor_fonte = CORES["texto_passado"]
        elif data_dt==agora.date() and inicio_dt <= agora <= fim_dt:
            borda = f"4px solid {CORES['borda_vermelha']}"
            badge = f"<span style='background:{CORES['badge_agora_bg']};color:{CORES['badge_agora_text']};padding:2px 6px;border-radius:5px;font-weight:bold;'>AGORA</span>"
        elif data_dt==agora.date():
            borda = f"3px solid {CORES['borda_amarela']}"
            badge = f"<span style='background:{CORES['badge_hoje_bg']};color:{CORES['badge_hoje_text']};padding:2px 6px;border-radius:5px;font-weight:bold;'>HOJE</span>"

        decoracao = "line-through" if status=="CANCELADO" else "none"
        motorista_html = f"🚗 {nome_motor} <a href='https://wa.me/{tel_motor}' target='_blank'>{tel_motor}</a><br>" if precisa_motor and tel_motor else ""

        st.markdown(f"""
        <div style="background:{cor_fundo};color:{cor_fonte};padding:16px;margin-bottom:10px;border-radius:10px;
            border:{borda};text-decoration:{decoracao};">
        <h3>{'👑' if agenda_pres else '📌'} {titulo} {badge}</h3>
        📅 {data_dt.strftime('%d/%m/%Y')} | ⏰ {hi_dt.strftime('%H:%M')} às {hf_dt.strftime('%H:%M')}<br>
        📍 {local}<br>🏠 {endereco}<br>🎥 {cobertura}<br>👥 {resp}<br>🎒 {equip}<br>
        {motorista_html}📝 {obs}<br><br><b>Status:</b> {status}
        </div>
        """, unsafe_allow_html=True)

        # Botões seguros
        c1,c2,c3 = st.columns(3)
        if c1.button("✏️ Editar", key=f"e_{eid}"):
            st.session_state.editando=True
            st.session_state.evento_id=eid
            st.experimental_rerun()
        if c2.button("❌ Cancelar/Reativar", key=f"c_{eid}"):
            novo="CANCELADO" if status=="ATIVO" else "ATIVO"
            cursor.execute("UPDATE eventos SET status=%s WHERE id=%s",(novo,eid))
            conn.commit()
            st.experimental_rerun()
        if c3.button("🗑 Apagar", key=f"d_{eid}"):
            cursor.execute("DELETE FROM eventos WHERE id=%s",(eid,))
            conn.commit()
            st.experimental_rerun()

# -----------------------------
# COMO RODAR
# -----------------------------
# pip install streamlit psycopg2 pandas reportlab
# streamlit run app.py
