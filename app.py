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
def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=st.secrets["DB_PORT"],
        sslmode=st.secrets["DB_SSLMODE"],
    )

conn = get_connection()
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
# ABA NOVO/EDITAR EVENTO
# -----------------------------
with aba_form:
    evento_db = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        evento_db = cursor.fetchone()
        st.warning(f"✏️ Editando evento ID: {st.session_state.evento_id}")
        if st.button("Cancelar Edição"):
            st.session_state.editando = False
            st.session_state.evento_id = None
            st.rerun()

    with st.form("form_evento", clear_on_submit=True):
        col_tipo1, col_tipo2 = st.columns(2)
        with col_tipo1:
            agenda_presidente = st.checkbox("👑 Agenda do Presidente?", value=bool(evento_db[1]) if evento_db else False)
        with col_tipo2:
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
        
        status = st.selectbox("Status", ["ATIVO", "CANCELADO"], index=0 if not evento_db or evento_db[15]=="ATIVO" else 1)

        submit = st.form_submit_button("💾 Salvar Evento")
        
        if submit:
            dados = (
                agenda_presidente, titulo, data_evento, hora_inicio, hora_fim,
                local, endereco, ", ".join(cobertura), responsaveis, equipamentos,
                observacoes, precisa_motorista, motorista_nome, motorista_telefone, status
            )
            
            if st.session_state.editando:
                cursor.execute("""
                    UPDATE eventos SET 
                    agenda_presidente=%s, titulo=%s, data=%s, hora_inicio=%s, hora_fim=%s,
                    local=%s, endereco=%s, cobertura=%s, responsaveis=%s, equipamentos=%s,
                    observacoes=%s, precisa_motorista=%s, motorista_nome=%s, motorista_telefone=%s, status=%s
                    WHERE id=%s
                """, dados + (st.session_state.evento_id,))
                st.success("Evento atualizado!")
                st.session_state.editando = False
                st.session_state.evento_id = None
            else:
                cursor.execute("""
                    INSERT INTO eventos (
                        agenda_presidente, titulo, data, hora_inicio, hora_fim,
                        local, endereco, cobertura, responsaveis, equipamentos,
                        observacoes, precisa_motorista, motorista_nome, motorista_telefone, status
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, dados)
                st.success("Evento criado!")
            
            conn.commit()
            st.rerun()

# -----------------------------
# ABA VISUALIZAR EVENTOS
# -----------------------------
with aba_eventos:
    # Filtros simples
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_data = st.date_input("Filtrar por data", value=None)
    with col_f2:
        filtro_tipo = st.selectbox("Tipo", ["Todos", "Presidente", "Outros"])

    query = "SELECT * FROM eventos WHERE 1=1"
    params = []
    if filtro_data:
        query += " AND data = %s"
        params.append(filtro_data)
    if filtro_tipo == "Presidente":
        query += " AND agenda_presidente = True"
    elif filtro_tipo == "Outros":
        query += " AND agenda_presidente = False"
    
    query += " ORDER BY data DESC, hora_inicio DESC"
    cursor.execute(query, tuple(params))
    eventos = cursor.fetchall()

    for ev in eventos:
        with st.expander(f"{'👑' if ev[1] else '📅'} {ev[3]} | {ev[2]} ({ev[15]})"):
            st.write(f"**Local:** {ev[6]} - {ev[7]}")
            st.write(f"**Horário:** {ev[4]} às {ev[5]}")
            st.write(f"**Responsáveis:** {ev[9]}")
            
            c1, c2, c3 = st.columns(3)
            if c1.button("Editar", key=f"ed_{ev[0]}"):
                st.session_state.editando = True
                st.session_state.evento_id = ev[0]
                st.rerun()
            
            status_acao = "CANCELADO" if ev[15] == "ATIVO" else "ATIVO"
            if c2.button(f"{status_acao}", key=f"st_{ev[0]}"):
                cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", (status_acao, ev[0]))
                conn.commit()
                st.rerun()
                
            if c3.button("Excluir", key=f"del_{ev[0]}"):
                cursor.execute("DELETE FROM eventos WHERE id=%s", (ev[0],))
                conn.commit()
                st.rerun()
