import streamlit as st
import psycopg2
from datetime import datetime, date, time, timedelta, timezone

# -----------------------------
# 1. CONFIGURAÇÃO DE CORES
# -----------------------------
COR_FUNDO_PRESIDENTE = "#2b488e"
COR_FUNDO_OUTRA = "#109439"
COR_FONTE_PRESIDENTE = "#ffffff"
COR_FONTE_OUTRA = "#ffffff"
COR_BORDA_HOJE = "#FFD700"
COR_BADGE_HOJE = "#FFD700"
COR_TEXTO_CANCELADO = "#6b6b6b"
COR_FUNDO_PASSADO = "#d9d9d9"
OPACIDADE_PASSADO = "0.6"

# -----------------------------
# 2. CONEXÃO POSTGRES (SUPABASE)
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
# 3. ESTADO DA PÁGINA
# -----------------------------
st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅", layout="wide")
st.title("📅 Agenda PRCOSET")

if "aba_atual" not in st.session_state:
    st.session_state.aba_atual = "LISTA"
if "editando" not in st.session_state:
    st.session_state.editando = False
if "evento_id" not in st.session_state:
    st.session_state.evento_id = None

# --- MENU DE BOTÕES NO TOPO ---
col_m1, col_m2, _ = st.columns([1, 1, 4])
with col_m1:
    if st.button("📋 Ver Eventos", use_container_width=True):
        st.session_state.aba_atual = "LISTA"
        st.rerun()
with col_m2:
    if st.button("📝 Novo Evento", use_container_width=True):
        st.session_state.aba_atual = "FORM"
        st.session_state.editando = False
        st.session_state.evento_id = None
        st.rerun()

st.markdown("---")

# -----------------------------
# 4. TELA DE FORMULÁRIO
# -----------------------------
if st.session_state.aba_atual == "FORM":
    evento_db = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        evento_db = cursor.fetchone()
        st.warning("✏️ Você está editando um evento.")

    with st.form("form_evento"):
        agenda_presidente = st.checkbox("👑 Agenda do Presidente?", value=bool(evento_db) if evento_db else False)
        precisa_motorista = st.checkbox("🚗 Precisa de motorista?", value=bool(evento_db) if evento_db else False)
        titulo = st.text_input("📝 Título", value=evento_db[2] if evento_db else "")

        c1, c2, c3 = st.columns(3)
        with c1: data_evento = st.date_input("📅 Data", value=evento_db[3] if evento_db else date.today())
        with c2: hora_inicio = st.time_input("⏰ Início", value=evento_db[4] if evento_db else time(9,0))
        with c3: hora_fim = st.time_input("⏰ Fim", value=evento_db[5] if evento_db else time(10,0))

        local = st.text_input("📍 Local", value=evento_db[6] if evento_db else "")
        endereco = st.text_input("🏠 Endereço", value=evento_db[7] if evento_db else "")
        cobertura = st.multiselect("🎥 Cobertura", ["Redes", "Foto", "Vídeo", "Imprensa"], 
                                   default=evento_db[8].split(", ") if evento_db and evento_db[8] else [])
        resp = st.text_input("👥 Responsáveis", value=evento_db[9] if evento_db else "")
        equip = st.text_input("🎒 Equipamentos", value=evento_db[10] if evento_db else "")
        obs = st.text_area("📝 Observações", value=evento_db[11] if evento_db else "")
        n_mot = st.text_input("Nome do motorista", value=evento_db[13] if evento_db else "")
        t_mot = st.text_input("Telefone motorista", value=evento_db[14] if evento_db else "")
        stat_f = st.selectbox("Status", ["ATIVO", "CANCELADO"], index=0 if not evento_db or evento_db[15]=="ATIVO" else 1)

        if st.form_submit_button("💾 Salvar"):
            dados = (bool(agenda_presidente), titulo, data_evento, hora_inicio, hora_fim, local, endereco, ", ".join(cobertura), resp, equip, obs, bool(precisa_motorista), n_mot, t_mot, stat_f)
            if st.session_state.editando:
                cursor.execute("UPDATE eventos SET agenda_presidente=%s, titulo=%s, data=%s, hora_inicio=%s, hora_fim=%s, local=%s, endereco=%s, cobertura=%s, responsaveis=%s, equipamentos=%s, observacoes=%s, precisa_motorista=%s, motorista_nome=%s, motorista_telefone=%s, status=%s WHERE id=%s", dados + (st.session_state.evento_id,))
            else:
                cursor.execute("INSERT INTO eventos (agenda_presidente, titulo, data, hora_inicio, hora_fim, local, endereco, cobertura, responsaveis, equipamentos, observacoes, precisa_motorista, motorista_nome, motorista_telefone, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", dados)
            conn.commit()
            st.session_state.aba_atual = "LISTA"
            st.rerun()

# -----------------------------
# 5. TELA DE LISTAGEM
# -----------------------------
elif st.session_state.aba_atual == "LISTA":
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: f_data = st.date_input("Data", value=None)
    with col_f2: f_agenda = st.selectbox("Agenda", ["Todas", "Presidente", "Outras"])
    with col_f3: f_resp = st.text_input("Responsável")

    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC")
    eventos = cursor.fetchall()
    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)

    for ev in eventos:
        eid, pres, tit, d_ev, hi, hf, loc, end, cob, resp, equip, obs, p_mot, n_mot, t_mot, stat = ev
        d_ev_dt = datetime.strptime(d_ev, "%Y-%m-%d").date() if isinstance(d_ev, str) else d_ev

        if f_data and d_ev_dt != f_data: continue
        if f_agenda == "Presidente" and not pres: continue
        if f_agenda == "Outras" and pres: continue
        if f_resp and f_resp.lower() not in (resp or "").lower(): continue

        cor_f = COR_FUNDO_PRESIDENTE if pres else COR_FUNDO_OUTRA
        opac = OPACIDADE_PASSADO if (d_ev_dt < agora.date()) else "1"
        link_zap = f"<br>🚗 <b>Motorista:</b> {n_mot} (<a href='https://wa.me{''.join(filter(str.isdigit, str(t_mot)))}' style='color:white;'>{t_mot}</a>)" if p_mot and t_mot else ""

        st.markdown(f"""
        <div style="background:{cor_f}; color:white; padding:20px; border-radius:12px; margin-bottom:10px; opacity:{opac}; border-left: 10px solid {'#FFD700' if pres else '#ffffff44'};">
            <h3 style="margin:0;">{'👑' if pres else '📌'} {tit} <span style="float:right; font-size:12px; background:rgba(0,0,0,0.3); padding:4px 10px; border-radius:20px;">{stat}</span></h3>
            <div style="margin-top:10px; font-size:15px; line-height:1.5;">
                <b>📅 {d_ev_dt.strftime('%d/%m/%Y')}</b> | ⏰ {hi} às {hf}<br>
                📍 {loc} | 🏠 {end}<br>
                🎥 {cob} | 👥 {resp}<br>
                🎒 {equip} {link_zap}
            </div>
            <div style="background: rgba(255,255,255,0.15); padding: 12px; border-radius: 8px; margin-top: 12px; font-size:14px;">📝 {obs}</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, _ = st.columns([1, 1.2, 1, 4])
        with c1:
            if st.button("✏️ Editar", key=f"ed_{eid}"):
                st.session_state.editando, st.session_state.evento_id = True, eid
                st.session_state.aba_atual = "FORM" # MUDA A TELA AQUI
                st.rerun()
        with c2:
            if st.button(f"🚫 Status", key=f"st_{eid}"):
                cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", ("CANCELADO" if stat=="ATIVO" else "ATIVO", eid))
                conn.commit(); st.rerun()
        with c3:
            if st.button("🗑️ Excluir", key=f"del_{eid}"):
                cursor.execute("DELETE FROM eventos WHERE id=%s", (eid,))
                conn.commit(); st.rerun()
        st.write("")
