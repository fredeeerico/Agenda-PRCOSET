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
# ESTADO GLOBAL
# -----------------------------
if "editando" not in st.session_state:
    st.session_state.editando = False
if "evento_id" not in st.session_state:
    st.session_state.evento_id = None

st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅", layout="wide")
st.title("📅 Agenda PRCOSET")

aba_eventos, aba_form = st.tabs(["📋 Eventos", "📝 Gerenciar Evento"])

# -----------------------------
# ABA FORMULÁRIO (NOVO / EDITAR)
# -----------------------------
with aba_form:
    evento_db = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        evento_db = cursor.fetchone()
        st.warning(f"✏️ Você está editando o evento: {evento_db[2] if evento_db else ''}")

    with st.form("form_evento"):
        # Conversão explícita para bool para evitar DatatypeMismatch
        agenda_presidente = st.checkbox("👑 Agenda do Presidente?", value=bool(evento_db[1]) if evento_db else False)
        precisa_motorista = st.checkbox("🚗 Precisa de motorista?", value=bool(evento_db[12]) if evento_db else False)
        titulo = st.text_input("📝 Título", value=evento_db[2] if evento_db else "")

        col1, col2, col3 = st.columns(3)
        with col1:
            data_evento = st.date_input("📅 Data", value=evento_db[3] if evento_db else date.today())
        with col2:
            hora_inicio = st.time_input("⏰ Início", value=evento_db[4] if evento_db else time(9,0))
        with col3:
            hora_fim = st.time_input("⏰ Fim", value=evento_db[5] if evento_db else time(10,0))

        local = st.text_input("📍 Local", value=evento_db[6] if evento_db else "")
        endereco = st.text_input("🏠 Endereço", value=evento_db[7] if evento_db else "")
        
        opcoes_cob = ["Redes", "Foto", "Vídeo", "Imprensa"]
        def_cob = evento_db[8].split(", ") if evento_db and evento_db[8] else []
        cobertura = st.multiselect("🎥 Cobertura", opcoes_cob, default=[c for c in def_cob if c in opcoes_cob])
        
        responsaveis = st.text_input("👥 Responsáveis", value=evento_db[9] if evento_db else "")
        equipamentos = st.text_input("🎒 Equipamentos", value=evento_db[10] if evento_db else "")
        observacoes = st.text_area("📝 Observações", value=evento_db[11] if evento_db else "")

        motorista_nome = st.text_input("Nome do motorista", value=evento_db[13] if evento_db else "")
        motorista_telefone = st.text_input("Telefone do motorista", value=evento_db[14] if evento_db else "")
        status_form = st.selectbox("Status", ["ATIVO", "CANCELADO"], index=0 if not evento_db or evento_db[15]=="ATIVO" else 1)

        if st.form_submit_button("💾 Salvar"):
            # Tuple de dados garantindo tipos corretos
            dados = (
                bool(agenda_presidente), titulo, data_evento, hora_inicio, hora_fim,
                local, endereco, ", ".join(cobertura), responsaveis, equipamentos,
                observacoes, bool(precisa_motorista), motorista_nome, motorista_telefone, status_form
            )
            
            if st.session_state.editando:
                cursor.execute("""
                UPDATE eventos SET agenda_presidente=%s, titulo=%s, data=%s, hora_inicio=%s, hora_fim=%s,
                local=%s, endereco=%s, cobertura=%s, responsaveis=%s, equipamentos=%s,
                observacoes=%s, precisa_motorista=%s, motorista_nome=%s, motorista_telefone=%s, status=%s
                WHERE id=%s""", dados + (st.session_state.evento_id,))
            else:
                cursor.execute("""
                INSERT INTO eventos (agenda_presidente, titulo, data, hora_inicio, hora_fim, local, endereco, 
                cobertura, responsaveis, equipamentos, observacoes, precisa_motorista, motorista_nome, 
                motorista_telefone, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", dados)
            
            conn.commit()
            st.session_state.editando = False
            st.session_state.evento_id = None
            st.rerun()

# -----------------------------
# ABA LISTAGEM (CARDS)
# -----------------------------
with aba_eventos:
    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: f_data = st.date_input("Filtrar Data", value=None)
    with col_f2: f_agenda = st.selectbox("Agenda", ["Todas", "Presidente", "Outras"])
    with col_f3: f_resp = st.text_input("Responsável")

    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC")
    eventos = cursor.fetchall()
    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)

    for ev in eventos:
        eid, pres, tit, d_ev, hi, hf, loc, end, cob, resp, equip, obs, p_mot, n_mot, t_mot, stat = ev

        # Filtros Lógica
        if f_data and d_ev != f_data: continue
        if f_agenda == "Presidente" and not pres: continue
        if f_agenda == "Outras" and pres: continue
        if f_resp and f_resp.lower() not in (resp or "").lower(): continue

        # Estilo do Card
        cor_fundo = COR_FUNDO_PRESIDENTE if pres else COR_FUNDO_OUTRA
        cor_fonte = COR_FONTE_PRESIDENTE if pres else COR_FONTE_OUTRA
        opacidade = OPACIDADE_PASSADO if (d_ev < agora.date()) else "1"
        decor = "line-through" if stat == "CANCELADO" else "none"
        
        # WhatsApp Link
        link_zap = f"<br>🚗 <b>Motorista:</b> {n_mot} (<a href='https://wa.me{t_mot}' style='color:{cor_fonte}'>{t_mot}</a>)" if p_mot and t_mot else ""

        st.markdown(f"""
        <div style="background:{cor_fundo}; color:{cor_fonte}; padding:20px; border-radius:12px; margin-bottom:15px; opacity:{opacidade}; text-decoration:{decor}; border-left: 8px solid {'#FFD700' if pres else '#fff'}; shadow: 2px 2px 5px rgba(0,0,0,0.2);">
            <h3 style="margin:0;">{'👑' if pres else '📌'} {tit} <span style="float:right; font-size:14px;">{stat}</span></h3>
            <hr style="border: 0.5px solid {cor_fonte}; opacity: 0.3;">
            <b>📅 Data:</b> {d_ev.strftime('%d/%m/%Y')} | <b>⏰ Horário:</b> {hi.strftime('%H:%M')} às {hf.strftime('%H:%M')}<br>
            <b>📍 Local:</b> {loc} | <b>🏠 Endereço:</b> {end}<br>
            <b>🎥 Cobertura:</b> {cob} | <b>👥 Responsáveis:</b> {resp}<br>
            <b>🎒 Equipamentos:</b> {equip} {link_zap}<br>
            <p style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-top: 10px;">📝 <b>Obs:</b> {obs}</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, _ = st.columns([1, 1, 1, 4])
        if c1.button("✏️ Editar", key=f"ed_{eid}"):
            st.session_state.editando, st.session_state.evento_id = True, eid
            st.rerun()
        if c2.button("🚫 Status", key=f"st_{eid}"):
            cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", ("CANCELADO" if stat=="ATIVO" else "ATIVO", eid))
            conn.commit(); st.rerun()
        if c3.button("🗑️ Excluir", key=f"del_{eid}"):
            cursor.execute("DELETE FROM eventos WHERE id=%s", (eid,))
            conn.commit(); st.rerun()
