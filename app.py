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
COR_FUNDO_PASSADO = "#d9d9d9"
OPACIDADE_PASSADO = "0.6"

# -----------------------------
# 2. CONEXÃO POSTGRES (SUPABASE)
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

# -----------------------------
# 3. ESTADO DA PÁGINA
# -----------------------------
st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅", layout="wide")

if "aba_atual" not in st.session_state:
    st.session_state.aba_atual = "LISTA"
if "editando" not in st.session_state:
    st.session_state.editando = False
if "evento_id" not in st.session_state:
    st.session_state.evento_id = None
if "mensagem_sucesso" not in st.session_state:
    st.session_state.mensagem_sucesso = None

st.title("📅 Agenda PRCOSET")

# --- MENU DE NAVEGAÇÃO ---
col_m1, col_m2, _ = st.columns([1, 1, 4])
with col_m1:
    if st.button("📋 Ver Lista", use_container_width=True):
        st.session_state.aba_atual = "LISTA"
        st.session_state.editando = False
        st.rerun()
with col_m2:
    if st.button("➕ Novo Evento", use_container_width=True):
        st.session_state.aba_atual = "FORM"
        st.session_state.editando = False
        st.session_state.evento_id = None
        st.rerun()

st.markdown("---")

if st.session_state.mensagem_sucesso:
    st.success(st.session_state.mensagem_sucesso)
    st.session_state.mensagem_sucesso = None

# -----------------------------
# 4. TELA DE FORMULÁRIO
# -----------------------------
if st.session_state.aba_atual == "FORM":
    evento_db = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        evento_db = cursor.fetchone()
        st.info("✨ Editando evento existente")

    with st.form("form_evento"):
        # Garantir valor booleano puro para os checkboxes
        v_pres = bool(evento_db[1]) if evento_db else False
        v_mot = bool(evento_db[12]) if evento_db else False
        
        c_tipo1, c_tipo2 = st.columns(2)
        with c_tipo1: agenda_pres = st.checkbox("👑 Agenda do Presidente?", value=v_pres)
        with c_tipo2: prec_mot = st.checkbox("🚗 Precisa de motorista?", value=v_mot)
        
        titulo = st.text_input("📝 Título", value=evento_db[2] if evento_db else "")

        c1, c2, c3 = st.columns(3)
        with c1: d_ev = st.date_input("📅 Data", value=evento_db[3] if evento_db else date.today())
        with c2: h_ini = st.time_input("⏰ Início", value=evento_db[4] if evento_db else time(9,0))
        with c3: h_fim = st.time_input("⏰ Fim", value=evento_db[5] if evento_db else time(10,0))

        loc = st.text_input("📍 Local", value=evento_db[6] if evento_db else "")
        end = st.text_input("🏠 Endereço", value=evento_db[7] if evento_db else "")
        
        cob_opcoes = ["Redes", "Foto", "Vídeo", "Imprensa"]
        cob_def = evento_db[8].split(", ") if evento_db and evento_db[8] else []
        cobertura = st.multiselect("🎥 Cobertura", cob_opcoes, default=[c for c in cob_def if c in cob_opcoes])
        
        responsáveis = st.text_input("👥 Responsáveis", value=evento_db[9] if evento_db else "")
        equipas = st.text_input("🎒 Equipamentos", value=evento_db[10] if evento_db else "")
        obs = st.text_area("📝 Observações", value=evento_db[11] if evento_db else "")
        
        n_m = st.text_input("Nome motorista", value=evento_db[13] if evento_db else "")
        t_m = st.text_input("Telefone motorista", value=evento_db[14] if evento_db else "")
        st_f = st.selectbox("Status", ["ATIVO", "CANCELADO"], index=0 if not evento_db or evento_db[15]=="ATIVO" else 1)

        if st.form_submit_button("💾 SALVAR"):
            # AQUI ESTÁ A CORREÇÃO: Forçamos bool() em todos os campos booleanos
            dados = (
                bool(agenda_pres), titulo, d_ev, h_ini, h_fim, 
                loc, end, ", ".join(cobertura), responsáveis, equipas, 
                obs, bool(prec_mot), n_m, t_m, st_f
            )
            
            if st.session_state.editando:
                cursor.execute("""
                    UPDATE eventos SET 
                    agenda_presidente=%s, titulo=%s, data=%s, hora_inicio=%s, hora_fim=%s, 
                    local=%s, endereco=%s, cobertura=%s, responsaveis=%s, equipamentos=%s, 
                    observacoes=%s, precisa_motorista=%s, motorista_nome=%s, motorista_telefone=%s, status=%s 
                    WHERE id=%s""", dados + (st.session_state.evento_id,))
            else:
                cursor.execute("""
                    INSERT INTO eventos (
                    agenda_presidente, titulo, data, hora_inicio, hora_fim, local, endereco, 
                    cobertura, responsaveis, equipamentos, observacoes, precisa_motorista, 
                    motorista_nome, motorista_telefone, status) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", dados)
            
            conn.commit()
            st.session_state.aba_atual = "LISTA"
            st.session_state.editando = False
            st.session_state.mensagem_sucesso = "Evento salvo com sucesso!"
            st.rerun()

# -----------------------------
# 5. TELA DE LISTAGEM
# -----------------------------
elif st.session_state.aba_atual == "LISTA":
    with st.expander("🔍 Filtros"):
        f1, f2 = st.columns(2)
        with f1: fil_data = st.date_input("Data", value=None)
        with f2: fil_agenda = st.selectbox("Agenda", ["Todas", "Presidente", "Outras"])

    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC")
    eventos = cursor.fetchall()
    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)

    for ev in eventos:
        eid, pres, tit, d_e, hi, hf, lo, en, co, re, eq, ob, pm, nm, tm, stt = ev
        d_dt = datetime.strptime(d_e, "%Y-%m-%d").date() if isinstance(d_e, str) else d_e

        if fil_data and d_dt != fil_data: continue
        if fil_agenda == "Presidente" and not pres: continue
        if fil_agenda == "Outras" and pres: continue

        cor = COR_FUNDO_PRESIDENTE if pres else COR_FUNDO_OUTRA
        opac = OPACIDADE_PASSADO if (d_dt < agora.date()) else "1"
        
        zap = f"<br>🚗 Motorista: {nm} (<a href='https://wa.me{''.join(filter(str.isdigit, str(tm)))}' style='color:white;'>{tm}</a>)" if pm and tm else ""

        st.markdown(f"""
        <div style="background:{cor}; color:white; padding:20px; border-radius:12px; margin-bottom:10px; opacity:{opac}; border-left: 10px solid {'#FFD700' if pres else '#ffffff44'};">
            <h3 style="margin:0;">{'👑' if pres else '📌'} {tit} <span style="float:right; font-size:12px;">{stt}</span></h3>
            <div style="margin-top:10px; font-size:15px;">
                <b>📅 {d_dt.strftime('%d/%m/%Y')}</b> | ⏰ {hi} às {hf}<br>
                📍 {lo} | 🏠 {en}<br>
                🎥 {co} | 👥 {re}<br>
                🎒 {eq} {zap}
            </div>
            <div style="background: rgba(255,255,255,0.15); padding: 10px; border-radius: 8px; margin-top: 10px; font-size:14px;">📝 {ob}</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, _ = st.columns([1, 1, 1, 4])
        with c1:
            if st.button("✏️ Editar", key=f"ed_{eid}"):
                st.session_state.editando, st.session_state.evento_id = True, eid
                st.session_state.aba_atual = "FORM"
                st.rerun()
        with c2:
            if st.button("🚫 Status", key=f"st_{eid}"):
                cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", ("CANCELADO" if stt=="ATIVO" else "ATIVO", eid))
                conn.commit(); st.rerun()
        with c3:
            if st.button("🗑️ Excluir", key=f"del_{eid}"):
                cursor.execute("DELETE FROM eventos WHERE id=%s", (eid,))
                conn.commit(); st.rerun()
