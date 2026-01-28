import streamlit as st
import psycopg2
from datetime import datetime, date, time, timedelta, timezone

# -----------------------------
# 1. CONFIGURAÇÃO E CONEXÃO
# -----------------------------
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=st.secrets["DB_PORT"],
        sslmode=st.secrets["DB_SSLMODE"],
    )

conn = init_connection()
cursor = conn.cursor()

st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅", layout="wide")

# Inicialização de estados
for key in ["aba_atual", "editando", "evento_id", "msg"]:
    if key not in st.session_state:
        st.session_state[key] = "LISTA" if key == "aba_atual" else None

st.title("📅 Agenda PRCOSET")

# Menu
c_m1, c_m2, _ = st.columns([1, 1, 3])
if c_m1.button("📋 Ver Lista", use_container_width=True):
    st.session_state.aba_atual = "LISTA"
    st.rerun()
if c_m2.button("➕ Novo Evento", use_container_width=True):
    st.session_state.aba_atual = "FORM"
    st.session_state.editando, st.session_state.evento_id = False, None
    st.rerun()

if st.session_state.msg:
    st.success(st.session_state.msg)
    st.session_state.msg = None

# -----------------------------
# 2. TELA DE FORMULÁRIO (CORREÇÃO SQL AQUI)
# -----------------------------
if st.session_state.aba_atual == "FORM":
    ev_db = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        ev_db = cursor.fetchone()

    with st.form("form_evento"):
        col_t = st.columns(2)
        pres_val = col_t[0].checkbox("👑 Agenda Presidente?", value=bool(ev_db[1]) if ev_db else False)
        mot_val = col_t[1].checkbox("🚗 Precisa Motorista?", value=bool(ev_db[12]) if ev_db else False)
        
        tit_val = st.text_input("📝 Título", value=ev_db[2] if ev_db else "")
        
        c = st.columns(3)
        data_val = c[0].date_input("📅 Data", value=ev_db[3] if ev_db else date.today())
        hi_val = c[1].time_input("⏰ Início", value=ev_db[4] if ev_db else time(9,0))
        hf_val = c[2].time_input("⏰ Fim", value=ev_db[5] if ev_db else time(10,0))

        loc_val = st.text_input("📍 Local", value=ev_db[6] if ev_db else "")
        end_val = st.text_input("🏠 Endereço", value=ev_db[7] if ev_db else "")
        cob_val = st.multiselect("🎥 Cobertura", ["Redes", "Foto", "Vídeo", "Imprensa"], 
                                 default=ev_db[8].split(", ") if ev_db and ev_db[8] else [])
        resp_val = st.text_input("👥 Responsáveis", value=ev_db[9] if ev_db else "")
        eq_val = st.text_input("🎒 Equipamentos", value=ev_db[10] if ev_db else "")
        obs_val = st.text_area("📝 Observações", value=ev_db[11] if ev_db else "")
        nm_val = st.text_input("Nome Motorista", value=ev_db[13] if ev_db else "")
        tm_val = st.text_input("Tel Motorista", value=ev_db[14] if ev_db else "")
        st_val = st.selectbox("Status", ["ATIVO", "CANCELADO"], index=0 if not ev_db or ev_db[15]=="ATIVO" else 1)

        if st.form_submit_button("💾 SALVAR"):
            # Dados organizados
            dados = (
                pres_val, tit_val, data_val, hi_val, hf_val,
                loc_val, end_val, ", ".join(cob_val), resp_val, eq_val,
                obs_val, mot_val, nm_val, tm_val, st_val
            )
            
            # SQL COM CAST EXPLÍCITO (::TIPO) PARA EVITAR DATATYPE MISMATCH
            if st.session_state.editando:
                cursor.execute("""
                    UPDATE eventos SET 
                    agenda_presidente=%s::BOOLEAN, titulo=%s, data=%s::DATE, 
                    hora_inicio=%s::TIME, hora_fim=%s::TIME, local=%s, endereco=%s, 
                    cobertura=%s, responsaveis=%s, equipamentos=%s, observacoes=%s, 
                    precisa_motorista=%s::BOOLEAN, motorista_nome=%s, motorista_telefone=%s, status=%s 
                    WHERE id=%s""", dados + (st.session_state.evento_id,))
            else:
                cursor.execute("""
                    INSERT INTO eventos (
                    agenda_presidente, titulo, data, hora_inicio, hora_fim, local, endereco, 
                    cobertura, responsaveis, equipamentos, observacoes, precisa_motorista, 
                    motorista_nome, motorista_telefone, status) 
                    VALUES (%s::BOOLEAN, %s, %s::DATE, %s::TIME, %s::TIME, %s, %s, %s, %s, %s, %s, %s::BOOLEAN, %s, %s, %s)""", dados)
            
            conn.commit()
            st.session_state.aba_atual, st.session_state.msg = "LISTA", "💾 Evento salvo com sucesso!"
            st.rerun()

# -----------------------------
# 3. TELA DE LISTAGEM
# -----------------------------
elif st.session_state.aba_atual == "LISTA":
    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC")
    eventos = cursor.fetchall()
    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)

    for ev in eventos:
        d_dt = ev[3] if isinstance(ev[3], date) else datetime.strptime(ev[3], "%Y-%m-%d").date()
        cor = "#2b488e" if ev[1] else "#109439"
        
        st.markdown(f"""
        <div style="background:{cor}; color:white; padding:20px; border-radius:12px; margin-bottom:10px; border-left: 10px solid {'#FFD700' if ev[1] else '#ffffff44'};">
            <h3 style="margin:0;">{'👑' if ev[1] else '📌'} {ev[2]} <span style="float:right; font-size:12px;">{ev[15]}</span></h3>
            <p style="margin-top:10px;"><b>📅 {d_dt.strftime('%d/%m/%Y')}</b> | ⏰ {ev[4]} às {ev[5]}<br>
            📍 {ev[6]} | 🎥 {ev[8]} | 👥 {ev[9]}</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, _ = st.columns([1, 1, 1, 4])
        if c1.button("✏️ Editar", key=f"e_{ev[0]}"):
            st.session_state.editando, st.session_state.evento_id, st.session_state.aba_atual = True, ev[0], "FORM"
            st.rerun()
        if c2.button("🚫 Status", key=f"s_{ev[0]}"):
            cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", ("CANCELADO" if ev[15]=="ATIVO" else "ATIVO", ev[0]))
            conn.commit(); st.rerun()
        if c3.button("🗑️ Excluir", key=f"d_{ev[0]}"):
            cursor.execute("DELETE FROM eventos WHERE id=%s", (ev[0],))
            conn.commit(); st.rerun()
