# app.py - Agenda PRCOSET Streamlit
# -----------------------------
# Funcionalidade completa:
# - Supabase/PostgreSQL
# - 10 eventos de teste automáticos
# - Cards pixel-perfect
# - Filtros por data, agenda e responsável
# - Botões Editar, Cancelar/Reativar e Apagar sem erro
# - Conversão segura de datas e horas
# - Seção de cores configurável
# -----------------------------

import streamlit as st
import psycopg2
from datetime import datetime, date, time, timedelta, timezone
import pandas as pd

# -----------------------------
# CONFIGURAÇÃO DE CORES (alterar aqui)
# -----------------------------
COR_FUNDO_PRESIDENTE = "#2b488e"
COR_FUNDO_OUTRA = "#109439"
COR_FONTE_PRESIDENTE = "#ffffff"
COR_FONTE_OUTRA = "#0f1116"
COR_BORDA_HOJE = "#FFD700"
COR_BORDA_AGORA = "#ff2b2b"
COR_BADGE_HOJE = "#FFD700"
COR_BADGE_AGORA = "#ff2b2b"
COR_TEXTO_CANCELADO = "#6b6b6b"
COR_FUNDO_PASSADO = "#d9d9d9"
OPACIDADE_PASSADO = "0.6"

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
# CRIAÇÃO TABELA EVENTOS
# -----------------------------
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
# INSERIR 10 EVENTOS DE TESTE (SE TABELA VAZIA)
# -----------------------------
cursor.execute("SELECT COUNT(*) FROM eventos")
if cursor.fetchone()[0] == 0:
    hoje = datetime.now(timezone(timedelta(hours=-3))).date()
    ontem = hoje - timedelta(days=1)
    semana_passada = hoje - timedelta(days=7)
    amanha = hoje + timedelta(days=1)
    proxima_semana = hoje + timedelta(days=7)

    eventos_teste = [
        # Ontem
        (True, "Reunião Estratégica", ontem, time(9,0), time(10,0), "Prefeitura", "Sala 1", "Redes, Foto", "Fred", "Câmera", "Obs", False, "", "", "ATIVO"),
        (False, "Visita Técnica", ontem, time(14,0), time(15,0), "Obra Central", "Endereço X", "Vídeo", "Ana", "Drone", "Obs", True, "Carlos", "11999999999", "ATIVO"),
        # Semana passada
        (True, "Coletiva de Imprensa", semana_passada, time(10,0), time(11,0), "Auditório", "Centro", "Imprensa", "Thais", "Microfone", "Obs", False, "", "", "CANCELADO"),
        (False, "Evento Comunitário", semana_passada, time(16,0), time(18,0), "Praça", "Bairro Y", "Foto", "Fred, Ana", "Câmera", "Obs", False, "", "", "ATIVO"),
        # Hoje
        (True, "Reunião com Secretários", hoje, time(8,0), time(9,30), "Gabinete", "Prefeitura", "Redes", "Fred, Thais", "Notebook", "Obs", True, "João", "11988888888", "ATIVO"),
        (False, "Entrega de Obras", hoje, time(11,0), time(12,0), "Obra Z", "Endereço Z", "Vídeo, Foto", "Ana", "Drone", "Obs", False, "", "", "ATIVO"),
        # Amanhã
        (True, "Agenda Oficial", amanha, time(9,0), time(10,0), "Gabinete", "Prefeitura", "Redes", "Fred", "Câmera", "Obs", False, "", "", "ATIVO"),
        (False, "Reunião Planejamento", amanha, time(15,0), time(16,0), "Sala 3", "Prefeitura", "Foto", "Thais", "Tripé", "Obs", False, "", "", "ATIVO"),
        # Próxima semana
        (True, "Evento Regional", proxima_semana, time(10,0), time(12,0), "Centro Eventos", "Centro", "Imprensa", "Fred, Ana, Thais", "Kit completo", "Obs", True, "Marcos", "11977777777", "ATIVO"),
        (False, "Visita Escolar", proxima_semana, time(14,0), time(15,30), "Escola ABC", "Bairro W", "Foto", "Ana", "Câmera", "Obs", False, "", "", "ATIVO"),
    ]

    for ev in eventos_teste:
        cursor.execute("""
        INSERT INTO eventos (
            agenda_presidente, titulo, data, hora_inicio, hora_fim,
            local, endereco, cobertura, responsaveis, equipamentos,
            observacoes, precisa_motorista, motorista_nome, motorista_telefone, status
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, ev)
    conn.commit()

# -----------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------
st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅", layout="centered")
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

# -----------------------------
# ABA NOVO EVENTO
# -----------------------------
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
        with col1:
            data_evento = st.date_input("📅 Data", value=evento[3] if evento else date.today())
        with col2:
            hora_inicio = st.time_input("⏰ Início", value=evento[4] if evento else time(9,0))
        with col3:
            hora_fim = st.time_input("⏰ Fim", value=evento[5] if evento else time(10,0))

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
                titulo, data_evento,
                hora_inicio, hora_fim,
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
                    observacoes=%s, precisa_motorista=%s, motorista_nome=%s, motorista_telefone=%s, status=%s
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
            st.experimental_rerun()

# -----------------------------
# ABA EVENTOS
# -----------------------------
with aba_eventos:
    col_filtro, col_lista = st.columns([1,3])
    with col_filtro:
        st.subheader("🔍 Filtros")
        filtro_data = st.date_input("📅 Data", value=None)
        filtro_agenda = st.selectbox("📂 Agenda", ["Todas","Agenda do Presidente","Outras agendas"])
        filtro_responsavel = st.text_input("👥 Responsável")

    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC, hora_fim ASC, agenda_presidente DESC")
    eventos = cursor.fetchall()

    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)
    hoje = agora.date()

    for ev in eventos:
        eid, agenda_pres, titulo, data_ev, hi, hf, local, endereco, cobertura, resp, equip, obs, precisa_motor, nome_motor, tel_motor, status = ev

        # --- CONVERSÃO SEGURA ---
        data_dt = data_ev if isinstance(data_ev, date) else datetime.strptime(str(data_ev), "%Y-%m-%d").date()
        hi_dt = hi if isinstance(hi, time) else datetime.strptime(str(hi), "%H:%M:%S").time()
        hf_dt = hf if isinstance(hf, time) else datetime.strptime(str(hf), "%H:%M:%S").time()
        inicio_dt = datetime.combine(data_dt, hi_dt)
        fim_dt = datetime.combine(data_dt, hf_dt)

        # --- Regras visuais ---
        cor_fundo = COR_FUNDO_PRESIDENTE if agenda_pres else COR_FUNDO_OUTRA
        cor_fonte = COR_FONTE_PRESIDENTE if agenda_pres else COR_FONTE_OUTRA
        borda = "none"
        badge = ""
        decoracao = "none"
        opacidade = "1"

        if status=="CANCELADO":
            decoracao="line-through"
            cor_fonte=COR_TEXTO_CANCELADO
        if data_dt < hoje or (data_dt==hoje and agora>fim_dt):
            cor_fundo = COR_FUNDO_PASSADO
            cor_fonte = COR_TEXTO_CANCELADO
            opacidade = OPACIDADE_PASSADO
        elif data_dt==hoje:
            badge = f"<span style='padding:2px 6px;border-radius:5px;font-weight:bold;background:{COR_BADGE_HOJE};color:#000;'>HOJE</span>"
            borda = f"3px solid {COR_BORDA_HOJE}"
            if inicio_dt <= agora <= fim_dt:
                badge = f"<span style='padding:2px 6px;border-radius:5px;font-weight:bold;background:{COR_BADGE_AGORA};color:#fff;'>AGORA</span>"
                borda = f"4px solid {COR_BORDA_AGORA}"

        # --- Motorista ---
        motorista_html = ""
        if precisa_motor and tel_motor:
            tel = tel_motor.replace(" ","").replace("-","").replace("(","").replace(")","")
            motorista_html = f"🚗 {nome_motor} <a href='https://wa.me/{tel}' target='_blank'>{tel_motor}</a><br>"

        # --- Filtros ---
        if filtro_data and data_dt != filtro_data:
            continue
        if filtro_agenda=="Agenda do Presidente" and not agenda_pres:
            continue
        if filtro_agenda=="Outras agendas" and agenda_pres:
            continue
        if filtro_responsavel and filtro_responsavel.lower() not in (resp or "").lower():
            continue

        # --- Renderização do card ---
        st.markdown(f"""
        <div style="background:{cor_fundo};color:{cor_fonte};opacity:{opacidade};
        padding:16px;border-radius:10px;margin-bottom:10px;
        border:{borda};text-decoration:{decoracao};">
        <h3>{'👑' if agenda_pres else '📌'} {titulo} {badge}</h3>
        📅 {data_dt.strftime('%d/%m/%Y')} | ⏰ {hi_dt.strftime('%H:%M')} às {hf_dt.strftime('%H:%M')}<br>
        📍 {local}<br>
        🏠 {endereco}<br>
        🎥 {cobertura}<br>
        👥 {resp}<br>
        🎒 {equip}<br>
        {motorista_html}
        📝 {obs}<br><br>
        <b>Status:</b> {status}
        </div>
        """, unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        if c1.button("✏️ Editar", key=f"edit{eid}"):
            st.session_state.editando=True
            st.session_state.evento_id=eid
            st.experimental_rerun()
        if c2.button("❌ Cancelar/Reativar", key=f"cancel{eid}"):
            novo_status = "CANCELADO" if status=="ATIVO" else "ATIVO"
            cursor.execute("UPDATE eventos SET status=%s WHERE id=%s",(novo_status,eid))
            conn.commit()
            st.experimental_rerun()
        if c3.button("🗑 Apagar", key=f"del{eid}"):
            cursor.execute("DELETE FROM eventos WHERE id=%s",(eid,))
            conn.commit()
            st.experimental_rerun()
