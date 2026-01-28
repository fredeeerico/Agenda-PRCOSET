import streamlit as st
import psycopg2
from datetime import datetime, date, time, timedelta, timezone

# -----------------------------
# CONFIGURAÇÃO DE CORES
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
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------
st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅", layout="wide")
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
aba_eventos, aba_form = st.tabs(["📋 Eventos", "📝 Gerenciar Evento"])

# -----------------------------
# ABA NOVO EVENTO / EDIÇÃO
# -----------------------------
with aba_form:
    evento = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        evento = cursor.fetchone()
        if evento:
            st.warning(f"✏️ Editando: {evento[2]}")
            if st.button("Cancelar Edição"):
                st.session_state.editando = False
                st.session_state.evento_id = None
                st.rerun()

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
        
        opcoes_cob = ["Redes", "Foto", "Vídeo", "Imprensa"]
        def_cob = evento[8].split(", ") if evento and evento[8] else []
        cobertura = st.multiselect("🎥 Cobertura", opcoes_cob, default=[c for c in def_cob if c in opcoes_cob])
        
        responsaveis = st.text_input("👥 Responsáveis", value=evento[9] if evento else "")
        equipamentos = st.text_input("🎒 Equipamentos", value=evento[10] if evento else "")
        observacoes = st.text_area("📝 Observações", value=evento[11] if evento else "")

        motorista_nome = st.text_input("Nome do motorista", value=evento[13] if evento else "")
        motorista_telefone = st.text_input("Telefone do motorista", value=evento[14] if evento else "")

        status_form = st.selectbox("Status", ["ATIVO", "CANCELADO"], index=0 if not evento or evento[15]=="ATIVO" else 1)

        if st.form_submit_button("💾 Salvar"):
            dados = (
                agenda_presidente, titulo, data_evento, hora_inicio, hora_fim,
                local, endereco, ", ".join(cobertura), responsaveis, equipamentos,
                observacoes, precisa_motorista, motorista_nome, motorista_telefone, status_form
            )
            if st.session_state.editando:
                cursor.execute("""
                UPDATE eventos SET agenda_presidente=%s, titulo=%s, data=%s, hora_inicio=%s, hora_fim=%s,
                local=%s, endereco=%s, cobertura=%s, responsaveis=%s, equipamentos=%s,
                observacoes=%s, precisa_motorista=%s, motorista_nome=%s, motorista_telefone=%s, status=%s
                WHERE id=%s """, dados + (st.session_state.evento_id,))
            else:
                cursor.execute("""
                INSERT INTO eventos (agenda_presidente, titulo, data, hora_inicio, hora_fim, local, endereco, 
                cobertura, responsaveis, equipamentos, observacoes, precisa_motorista, motorista_nome, 
                motorista_telefone, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", dados)
            
            conn.commit()
            st.session_state.editando = False
            st.session_state.evento_id = None
            st.success("Sucesso!")
            st.rerun()

# -----------------------------
# ABA VISUALIZAÇÃO
# -----------------------------
with aba_eventos:
    col_filtro, col_lista = st.columns([1,3])
    with col_filtro:
        st.subheader("🔍 Filtros")
        filtro_data = st.date_input("📅 Data", value=None)
        filtro_agenda = st.selectbox("📂 Agenda", ["Todas","Agenda do Presidente","Outras agendas"])
        filtro_resp = st.text_input("👥 Responsável")

    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC")
    eventos = cursor.fetchall()
    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)
    hoje = agora.date()

    with col_lista:
        for ev in eventos:
            eid, agenda_pres, titulo, data_ev, hi, hf, local, endereco, cob, resp, equip, obs, p_mot, n_mot, t_mot, status = ev
            
            # Filtros
            if filtro_data and data_ev != filtro_data: continue
            if filtro_agenda=="Agenda do Presidente" and not agenda_pres: continue
            if filtro_agenda=="Outras agendas" and agenda_pres: continue
            if filtro_resp and filtro_resp.lower() not in (resp or "").lower(): continue

            # Lógica de cores/cards
            cor_fundo = COR_FUNDO_PRESIDENTE if agenda_pres else COR_FUNDO_OUTRA
            cor_fonte = COR_FONTE_PRESIDENTE if agenda_pres else COR_FONTE_OUTRA
            borda, badge, opacidade, decor = "none", "", "1", "none"

            if status=="CANCELADO": 
                decor, cor_fonte = "line-through", COR_TEXTO_CANCELADO
            
            # Render Card (Simplificado para o exemplo)
            st.markdown(f"""
            <div style="background:{cor_fundo}; color:{cor_fonte}; padding:15px; border-radius:10px; margin-bottom:10px; text-decoration:{decor}; border:{borda};">
                <h4>{'👑' if agenda_pres else '📅'} {titulo}</h4>
                <p>📍 {local} | ⏰ {hi} - {hf}</p>
                <small>{resp} | {cob}</small>
            </div>
            """, unsafe_allow_html=True)

            # Botões de Ação
            b1, b2, b3 = st.columns(3)
            if b1.button("✏️ Editar", key=f"ed_{eid}"):
                st.session_state.editando = True
                st.session_state.evento_id = eid
                st.rerun()
            
            if b2.button("🚫 Status", key=f"st_{eid}"):
                novo = "CANCELADO" if status=="ATIVO" else "ATIVO"
                cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", (novo, eid))
                conn.commit()
                st.rerun()

            if b3.button("🗑️ Apagar", key=f"del_{eid}"):
                cursor.execute("DELETE FROM eventos WHERE id=%s", (eid,))
                conn.commit()
                st.rerun()
