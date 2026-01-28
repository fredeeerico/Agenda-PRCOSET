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
COR_BORDA_AGORA = "#ff2b2b"
COR_BADGE_HOJE = "#FFD700"
COR_BADGE_AGORA = "#ff2b2b"
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
# 3. ESTADO DA PÁGINA
# -----------------------------
st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅", layout="wide")
st.title("📅 Agenda PRCOSET")

if "editando" not in st.session_state:
    st.session_state.editando = False
if "evento_id" not in st.session_state:
    st.session_state.evento_id = None

aba_eventos, aba_form = st.tabs(["📋 Lista de Eventos", "📝 Gerenciar Evento"])

# -----------------------------
# Função Auxiliar: parsing seguro de hora
# -----------------------------
def safe_time_parse(h):
    if isinstance(h, time):
        return h
    h_str = str(h)
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(h_str, fmt).time()
        except ValueError:
            continue
    return time(0,0)

# -----------------------------
# 4. ABA FORMULÁRIO
# -----------------------------
with aba_form:
    evento_db = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        evento_db = cursor.fetchone()
        st.warning(f"✏️ Modo Edição Ativado")

        def cancelar_edicao():
            st.session_state.editando = False
            st.session_state.evento_id = None
            st.experimental_rerun()

        st.button("Cancelar Edição", on_click=cancelar_edicao)

    with st.form("form_evento"):
        agenda_presidente = st.checkbox(
            "👑 Agenda do Presidente?", 
            value=bool(evento_db[1]) if evento_db else False
        )
        precisa_motorista = st.checkbox(
            "🚗 Precisa de motorista?", 
            value=bool(evento_db[12]) if evento_db else False
        )
        titulo = st.text_input("📝 Título", value=evento_db[2] if evento_db else "")

        col1, col2, col3 = st.columns(3)
        with col1:
            data_evento = st.date_input("📅 Data", value=evento_db[3] if evento_db else date.today())
        with col2:
            hora_inicio = st.time_input(
                "⏰ Início", 
                value=safe_time_parse(evento_db[4]) if evento_db else time(9,0)
            )
        with col3:
            hora_fim = st.time_input(
                "⏰ Fim", 
                value=safe_time_parse(evento_db[5]) if evento_db else time(10,0)
            )

        local = st.text_input("📍 Local", value=evento_db[6] if evento_db else "")
        endereco = st.text_input("🏠 Endereço", value=evento_db[7] if evento_db else "")

        opcoes_cob = ["Redes", "Foto", "Vídeo", "Imprensa"]
        def_cob = evento_db[8].split(", ") if evento_db and evento_db[8] else []
        cobertura = st.multiselect(
            "🎥 Cobertura", 
            opcoes_cob, 
            default=[c for c in def_cob if c in opcoes_cob]
        )

        responsaveis = st.text_input("👥 Responsáveis", value=evento_db[9] if evento_db else "")
        equipamentos = st.text_input("🎒 Equipamentos", value=evento_db[10] if evento_db else "")
        observacoes = st.text_area("📝 Observações", value=evento_db[11] if evento_db else "")

        motorista_nome = st.text_input("Nome do motorista", value=evento_db[13] if evento_db else "")
        motorista_telefone = st.text_input("Telefone do motorista", value=evento_db[14] if evento_db else "")
        status_form = st.selectbox(
            "Status", 
            ["ATIVO", "CANCELADO"], 
            index=0 if not evento_db or evento_db[15]=="ATIVO" else 1
        )

        def salvar_evento():
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
                    WHERE id=%s
                """, dados + (st.session_state.evento_id,))
            else:
                cursor.execute("""
                    INSERT INTO eventos (agenda_presidente, titulo, data, hora_inicio, hora_fim, local, endereco, 
                    cobertura, responsaveis, equipamentos, observacoes, precisa_motorista, motorista_nome, 
                    motorista_telefone, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, dados)
            conn.commit()
            st.session_state.editando = False
            st.session_state.evento_id = None
            st.success("Evento salvo com sucesso!")
            st.experimental_rerun()

        st.form_submit_button("💾 Salvar Informações", on_click=salvar_evento)

# -----------------------------
# 5. ABA LISTAGEM (CARDS)
# -----------------------------
with aba_eventos:
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: f_data = st.date_input("Filtrar por Data", value=None)
    with col_f2: f_agenda = st.selectbox("Filtrar Agenda", ["Todas", "Agenda do Presidente", "Outras Agendas"])
    with col_f3: f_resp = st.text_input("Buscar Responsável")

    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC")
    eventos = cursor.fetchall()
    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)

    for ev in eventos:
        eid, pres, tit, d_ev, hi, hf, loc, end, cob, resp, equip, obs, p_mot, n_mot, t_mot, stat = ev
        d_ev_dt = datetime.strptime(d_ev, "%Y-%m-%d").date() if isinstance(d_ev, str) else d_ev
        hi_dt = safe_time_parse(hi)
        hf_dt = safe_time_parse(hf)

        # Aplicar Filtros
        if f_data and d_ev_dt != f_data: continue
        if f_agenda == "Agenda do Presidente" and not pres: continue
        if f_agenda == "Outras Agendas" and pres: continue
        if f_resp and f_resp.lower() not in (resp or "").lower(): continue

        # Estilo do Card
        cor_fundo = COR_FUNDO_PRESIDENTE if pres else COR_FUNDO_OUTRA
        cor_fonte = COR_FONTE_PRESIDENTE if pres else COR_FONTE_OUTRA
        opacidade = OPACIDADE_PASSADO if (d_ev_dt < agora.date()) else "1"
        decor = "line-through" if stat == "CANCELADO" else "none"

        # WhatsApp Link
        link_zap = ""
        if p_mot and t_mot:
            tel_limpo = "".join(filter(str.isdigit, str(t_mot)))
            link_zap = f"<br>🚗 <b>Motorista:</b> {n_mot} (<a href='https://wa.me/{tel_limpo}' style='color:white;'>{t_mot}</a>)"

        st.markdown(f"""
        <div style="background:{cor_fundo}; color:{cor_fonte}; padding:20px; border-radius:12px; margin-bottom:10px; opacity:{opacidade}; text-decoration:{decor}; border-left: 10px solid {'#FFD700' if pres else '#ffffff44'};">
            <h3 style="margin:0;">{'👑 PRESIDENTE:' if pres else '📌 EVENTO:'} {tit} <span style="float:right; font-size:12px; background:rgba(0,0,0,0.3); padding:4px 10px; border-radius:20px;">{stat}</span></h3>
            <div style="margin-top:10px; font-size:15px; line-height:1.5;">
                <b>📅 Data:</b> {d_ev_dt.strftime('%d/%m/%Y')} | <b>⏰ Hora:</b> {hi_dt.strftime('%H:%M')} às {hf_dt.strftime('%H:%M')}<br>
                <b>📍 Local:</b> {loc} | <b>🏠 Endereço:</b> {end}<br>
                <b>🎥 Cobertura:</b> {cob} | <b>👥 Responsáveis:</b> {resp}<br>
                <b>🎒 Equipamentos:</b> {equip} {link_zap}
            </div>
            <div style="background: rgba(255,255,255,0.15); padding: 12px; border-radius: 8px; margin-top: 12px; font-size:14px;">
                <b>📝 Observações:</b> {obs if obs else "Nenhuma."}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Funções para botões
        def editar_evento(eid=eid):
            st.session_state.editando = True
            st.session_state.evento_id = eid
            st.experimental_rerun()

        def alternar_status(eid=eid, stat=stat):
            novo_status = "ATIVO" if stat=="CANCELADO" else "CANCELADO"
            cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", (novo_status, eid))
            conn.commit()
            st.experimental_rerun()

        def excluir_evento(eid=eid):
            cursor.execute("DELETE FROM eventos WHERE id=%s", (eid,))
            conn.commit()
            st.experimental_rerun()

        c1, c2, c3, _ = st.columns([1,1.2,1,4])
        c1.button("✏️ Editar", key=f"ed_{eid}", on_click=editar_evento)
        label_bt = "Ativar" if stat == "CANCELADO" else "Cancelar"
        c2.button(f"🚫 {label_bt}", key=f"st_{eid}", on_click=alternar_status)
        c3.button("🗑️ Excluir", key=f"del_{eid}", on_click=excluir_evento)
        st.write("")  # Espaçador
