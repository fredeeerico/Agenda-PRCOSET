import streamlit as st
import psycopg2
from datetime import date, time, datetime, timedelta, timezone

# -----------------------------
# CONEXÃO SUPABASE (PostgreSQL)
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
# CRIAR TABELA SE NÃO EXISTIR
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
# CRIAR 10 EVENTOS DE TESTE SE A TABELA ESTIVER VAZIA
# -----------------------------
cursor.execute("SELECT COUNT(*) FROM eventos")
total_eventos = cursor.fetchone()[0]

if total_eventos == 0:
    tz = timezone(timedelta(hours=-3))  # UTC-3 Brasil
    hoje = datetime.now(tz).date()
    ontem = hoje - timedelta(days=1)
    semana_passada = hoje - timedelta(days=7)
    amanha = hoje + timedelta(days=1)
    proxima_semana = hoje + timedelta(days=7)

    eventos_teste = [
        # Semana passada
        (True,"Coletiva de Imprensa", semana_passada, time(10,0), time(11,0),"Auditório","Centro","Imprensa","Thais", "Microfone","Obs", False,"","", "CANCELADO"),
        (False,"Evento Comunitário", semana_passada, time(16,0), time(18,0),"Praça","Bairro Y","Foto","Fred, Ana","Câmera","Obs", False,"","", "ATIVO"),

        # Ontem
        (True,"Reunião Estratégica", ontem, time(9,0), time(10,0),"Prefeitura","Sala 1","Redes, Foto","Fred","Câmera","Obs", False,"","", "ATIVO"),
        (False,"Visita Técnica", ontem, time(14,0), time(15,0),"Obra Central","Endereço X","Vídeo","Ana","Drone","Obs", True,"Carlos","11999999999","ATIVO"),

        # Hoje já encerrado
        (False,"Entrega de Obras", hoje, time(8,0), time(9,0),"Obra Z","Endereço Z","Vídeo, Foto","Ana","Drone","Obs", False,"","", "ATIVO"),

        # Hoje AGORA
        (True,"Reunião com Secretários", hoje, time(9,0), time(18,0),"Gabinete","Prefeitura","Redes","Fred, Thais","Notebook","Obs", True,"João","11988888888","ATIVO"),

        # Amanhã
        (True,"Agenda Oficial", amanha, time(9,0), time(10,0),"Gabinete","Prefeitura","Redes","Fred","Câmera","Obs", False,"","", "ATIVO"),
        (False,"Reunião Planejamento", amanha, time(15,0), time(16,0),"Sala 3","Prefeitura","Foto","Thais","Tripé","Obs", False,"","", "ATIVO"),

        # Próxima semana
        (True,"Evento Regional", proxima_semana, time(10,0), time(12,0),"Centro Eventos","Centro","Imprensa","Fred, Ana, Thais","Kit completo","Obs", True,"Marcos","11977777777","ATIVO"),
        (False,"Visita Escolar", proxima_semana, time(14,0), time(15,30),"Escola ABC","Bairro W","Foto","Ana","Câmera","Obs", False,"","", "ATIVO"),
    ]

    for ev in eventos_teste:
        cursor.execute("""
        INSERT INTO eventos (
            agenda_presidente, titulo, data, hora_inicio, hora_fim,
            local, endereco, cobertura, responsaveis, equipamentos,
            observacoes, precisa_motorista, motorista_nome, motorista_telefone, status
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            ev[0], ev[1], ev[2], ev[3], ev[4], ev[5], ev[6], ev[7],
            ev[8], ev[9], ev[10], ev[11], ev[12], ev[13], ev[14]
        ))
    conn.commit()
    st.info("🔹 10 eventos de teste criados automaticamente!")

# -----------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------
st.set_page_config(
    page_title="Agenda PRCOSET",
    page_icon="📅",
    layout="centered"
)

st.title("📅 Agenda PRCOSET")

# -----------------------------
# ESTADO GLOBAL
# -----------------------------
if "editando" not in st.session_state:
    st.session_state.editando = False
if "evento_id" not in st.session_state:
    st.session_state.evento_id = None
if "aba_ativa" not in st.session_state:
    st.session_state.aba_ativa = "📋 Eventos"

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
        cursor.execute("""
        SELECT * FROM eventos WHERE id=%s
        """, (st.session_state.evento_id,))
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
            st.session_state.aba_ativa = "📋 Eventos"
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

    cursor.execute("""
    SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC
    """)
    eventos = cursor.fetchall()

    tz = timezone(timedelta(hours=-3))
    hoje = datetime.now(tz).date()
    agora = datetime.now(tz).time()

    eventos_visiveis = []
    for ev in eventos:
        data_ev = ev[3]
        if filtro_data and data_ev != filtro_data:
            continue
        if filtro_agenda=="Agenda do Presidente" and not ev[1]:
            continue
        if filtro_agenda=="Outras agendas" and ev[1]:
            continue
        if filtro_responsavel and filtro_responsavel.lower() not in (ev[9] or "").lower():
            continue
        eventos_visiveis.append(ev)

    for ev in eventos_visiveis:
        id_ev, agenda_presidente, titulo, data_ev, hi, hf, local, endereco, cobertura, resp, equip, obs, precisa_m, mot_nome, mot_tel, status = ev
        data_dt = data_ev
        hi_dt = hi
        hf_dt = hf

        # Determinar cores e badges
        cor_fundo = "#2b488e" if agenda_presidente else "#109439"
        cor_fonte = "#fff" if agenda_presidente else "#0f1116"
        borda = "none"
        badge = ""
        decoracao = "line-through" if status=="CANCELADO" else "none"

        if data_dt < hoje:
            cor_fundo = "#d9d9d9"; cor_fonte="#6b6b6b"; opacidade="0.6"
        elif data_dt==hoje and hf_dt <= agora:
            cor_fundo = "#d9d9d9"; cor_fonte="#6b6b6b"; opacidade="0.6"; borda="3px solid #FFD700"; badge="<span style='padding:2px 6px;border-radius:5px;font-weight:bold;background:#FFD700;color:#000;'>HOJE</span>"
        elif data_dt==hoje and hi_dt <= agora <= hf_dt:
            borda="4px solid #ff2b2b"; badge="<span style='padding:2px 6px;border-radius:5px;font-weight:bold;background:#ff2b2b;color:#fff;'>AGORA</span>"

        mot_html = f"🚗 {mot_nome} <a href='https://wa.me/{mot_tel}' target='_blank'>{mot_tel}</a><br>" if precisa_m and mot_tel else ""

        st.markdown(f"""
        <div style="background:{cor_fundo};color:{cor_fonte};
            padding:16px;border-radius:10px;margin-bottom:10px;
            border:{borda};text-decoration:{decoracao};">
            <h3>{"👑" if agenda_presidente else "📌"} {titulo} {badge}</h3>
            📅 {data_dt.strftime('%d/%m/%Y')} | ⏰ {hi_dt.strftime('%H:%M')} às {hf_dt.strftime('%H:%M')}<br>
            📍 {local}<br>🏠 {endereco}<br>🎥 {cobertura}<br>👥 {resp}<br>🎒 {equip}<br>
            {mot_html}📝 {obs}<br><br>
            <b>Status:</b> {status}
        </div>
        """, unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        if c1.button("✏️ Editar", key=f"e{id_ev}"):
            st.session_state.editando = True
            st.session_state.evento_id = id_ev
            st.experimental_rerun()
        if c2.button("❌ Cancelar/Reativar", key=f"c{id_ev}"):
            novo_status = "CANCELADO" if status=="ATIVO" else "ATIVO"
            cursor.execute("UPDATE eventos SET status=%s WHERE id=%s",(novo_status,id_ev))
            conn.commit()
            st.experimental_rerun()
        if c3.button("🗑 Apagar", key=f"d{id_ev}"):
            cursor.execute("DELETE FROM eventos WHERE id=%s",(id_ev,))
            conn.commit()
            st.experimental_rerun()
