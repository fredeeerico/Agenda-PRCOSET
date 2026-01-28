# app.py
import streamlit as st
import psycopg2
from datetime import datetime, date, time, timedelta, timezone

# ==============================
# CONEXÃO COM SUPABASE (POSTGRESQL)
# ==============================
conn = psycopg2.connect(
    host=st.secrets["DB_HOST"],
    database=st.secrets["DB_NAME"],
    user=st.secrets["DB_USER"],
    password=st.secrets["DB_PASSWORD"],
    port=st.secrets["DB_PORT"],
    sslmode=st.secrets["DB_SSLMODE"]
)
cursor = conn.cursor()

# ==============================
# CRIAR TABELA SE NÃO EXISTIR
# ==============================
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

# ==============================
# INSERIR 10 EVENTOS DE TESTE SE TABELA VAZIA
# ==============================
cursor.execute("SELECT COUNT(*) FROM eventos")
if cursor.fetchone()[0] == 0:
    agora = datetime.now(timezone(timedelta(hours=-3)))
    hoje = agora.date()
    ontem = hoje - timedelta(days=1)
    semana_passada = hoje - timedelta(days=7)
    amanha = hoje + timedelta(days=1)
    proxima_semana = hoje + timedelta(days=7)

    eventos_teste = [
        # Ontem
        (True,"Reunião Estratégica",ontem,time(9,0),time(10,0),"Prefeitura","Sala 1","Redes, Foto","Fred","Câmera","Obs",False,"","","ATIVO"),
        (False,"Visita Técnica",ontem,time(14,0),time(15,0),"Obra Central","Endereço X","Vídeo","Ana","Drone","Obs",True,"Carlos","11999999999","ATIVO"),
        # Semana passada
        (True,"Coletiva de Imprensa",semana_passada,time(10,0),time(11,0),"Auditório","Centro","Imprensa","Thais","Microfone","Obs",False,"","","CANCELADO"),
        (False,"Evento Comunitário",semana_passada,time(16,0),time(18,0),"Praça","Bairro Y","Foto","Fred, Ana","Câmera","Obs",False,"","","ATIVO"),
        # Hoje
        (True,"Reunião com Secretários",hoje,time(8,0),time(9,30),"Gabinete","Prefeitura","Redes","Fred, Thais","Notebook","Obs",True,"João","11988888888","ATIVO"),
        (False,"Entrega de Obras",hoje,time(11,0),time(12,0),"Obra Z","Endereço Z","Vídeo, Foto","Ana","Drone","Obs",False,"","","ATIVO"),
        (False,"Evento AGORA",hoje,agora.time(),(agora+timedelta(hours=1)).time(),"Centro Eventos","Centro","Foto","Fred, Ana","Kit","Obs",False,"","","ATIVO"),
        # Amanhã
        (True,"Agenda Oficial",amanha,time(9,0),time(10,0),"Gabinete","Prefeitura","Redes","Fred","Câmera","Obs",False,"","","ATIVO"),
        (False,"Reunião Planejamento",amanha,time(15,0),time(16,0),"Sala 3","Prefeitura","Foto","Thais","Tripé","Obs",False,"","","ATIVO"),
        # Próxima semana
        (True,"Evento Regional",proxima_semana,time(10,0),time(12,0),"Centro Eventos","Centro","Imprensa","Fred, Ana, Thais","Kit completo","Obs",True,"Marcos","11977777777","ATIVO"),
        (False,"Visita Escolar",proxima_semana,time(14,0),time(15,30),"Escola ABC","Bairro W","Foto","Ana","Câmera","Obs",False,"","","ATIVO"),
    ]

    for ev in eventos_teste:
        cursor.execute("""
        INSERT INTO eventos (agenda_presidente,titulo,data,hora_inicio,hora_fim,
            local,endereco,cobertura,responsaveis,equipamentos,observacoes,
            precisa_motorista,motorista_nome,motorista_telefone,status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, ev)
    conn.commit()

# ==============================
# CONFIGURAÇÃO STREAMLIT
# ==============================
st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅", layout="centered")
st.title("📅 Agenda PRCOSET")

# ==============================
# ESTADO GLOBAL
# ==============================
if "editando" not in st.session_state:
    st.session_state.editando=False
if "evento_id" not in st.session_state:
    st.session_state.evento_id=None

# ==============================
# ABAS
# ==============================
aba_eventos, aba_form = st.tabs(["📋 Eventos","📝 Novo Evento"])

# =====================================================
# 📝 ABA NOVO EVENTO
# =====================================================
with aba_form:
    evento = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("SELECT * FROM eventos WHERE id=%s",(st.session_state.evento_id,))
        evento = cursor.fetchone()
        st.warning("✏️ Você está editando um evento já existente.")

    with st.form("form_evento"):
        agenda_presidente = st.checkbox("👑 Agenda do Presidente?", value=bool(evento[1]) if evento else False)
        precisa_motorista = st.checkbox("🚗 Precisa de motorista?", value=bool(evento[12]) if evento else False)
        titulo = st.text_input("📝 Título", value=evento[2] if evento else "")
        col1,col2,col3 = st.columns(3)
        with col1:
            data_evento = st.date_input("📅 Data", value=evento[3] if evento else date.today())
        with col2:
            hora_inicio = st.time_input("⏰ Início", value=evento[4] if evento else time(9,0))
        with col3:
            hora_fim = st.time_input("⏰ Fim", value=evento[5] if evento else time(10,0))
        local = st.text_input("📍 Local", value=evento[6] if evento else "")
        endereco = st.text_input("🏠 Endereço", value=evento[7] if evento else "")
        cobertura = st.multiselect("🎥 Cobertura", ["Redes","Foto","Vídeo","Imprensa"], default=evento[8].split(", ") if evento and evento[8] else [])
        responsaveis = st.text_input("👥 Responsáveis", value=evento[9] if evento else "")
        equipamentos = st.text_input("🎒 Equipamentos", value=evento[10] if evento else "")
        observacoes = st.text_area("📝 Observações", value=evento[11] if evento else "")

        motorista_nome=""
        motorista_telefone=""
        if precisa_motorista:
            motorista_nome = st.text_input("Nome do motorista", value=evento[13] if evento else "")
            motorista_telefone = st.text_input("Telefone do motorista", value=evento[14] if evento else "")

        status = st.selectbox("Status",["ATIVO","CANCELADO"], index=0 if not evento or evento[15]=="ATIVO" else 1)

        if st.form_submit_button("💾 Salvar"):
            dados = (
                agenda_presidente,
                titulo,
                data_evento,
                hora_inicio,
                hora_fim,
                local,
                endereco,
                ", ".join(cobertura),
                responsaveis,
                equipamentos,
                observacoes,
                precisa_motorista,
                motorista_nome,
                motorista_telefone,
                status
            )
            if evento:
                cursor.execute("""
                UPDATE eventos SET agenda_presidente=%s,titulo=%s,data=%s,hora_inicio=%s,hora_fim=%s,
                    local=%s,endereco=%s,cobertura=%s,responsaveis=%s,equipamentos=%s,
                    observacoes=%s,precisa_motorista=%s,motorista_nome=%s,motorista_telefone=%s,status=%s
                    WHERE id=%s
                """, dados + (st.session_state.evento_id,))
            else:
                cursor.execute("""
                INSERT INTO eventos (agenda_presidente,titulo,data,hora_inicio,hora_fim,
                    local,endereco,cobertura,responsaveis,equipamentos,observacoes,
                    precisa_motorista,motorista_nome,motorista_telefone,status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, dados)
            conn.commit()
            st.session_state.editando=False
            st.session_state.evento_id=None
            st.experimental_rerun()

# =====================================================
# 📋 ABA EVENTOS
# =====================================================
with aba_eventos:
    col_filtro,col_lista = st.columns([1,3])
    with col_filtro:
        st.subheader("🔍 Filtros")
        filtro_data = st.date_input("📅 Data", value=None)
        filtro_agenda = st.selectbox("📂 Tipo de agenda", ["Todas","Agenda do Presidente","Outras agendas"])
        filtro_responsavel = st.text_input("👥 Responsável")

    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC")
    eventos = cursor.fetchall()

    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)
    hoje = agora.date()

    for ev in eventos:
        id_ev, agenda_presidente, titulo, data_ev, hi, hf, local, endereco, cobertura, resp, equip, obs, precisa_m, mot_nome, mot_tel, status = ev

        # Conversão de hora
        if isinstance(data_ev,str):
            data_ev=datetime.strptime(data_ev,"%Y-%m-%d").date()
        if isinstance(hi,str):
            hi=datetime.strptime(hi,"%H:%M:%S").time() if len(hi.split(":"))==3 else datetime.strptime(hi,"%H:%M").time()
        if isinstance(hf,str):
            hf=datetime.strptime(hf,"%H:%M:%S").time() if len(hf.split(":"))==3 else datetime.strptime(hf,"%H:%M").time()

        inicio_dt = datetime.combine(data_ev,hi)
        fim_dt = datetime.combine(data_ev,hf)

        # Aplicar filtros
        if filtro_data and data_ev!=filtro_data:
            continue
        if filtro_agenda=="Agenda do Presidente" and not agenda_presidente:
            continue
        if filtro_agenda=="Outras agendas" and agenda_presidente:
            continue
        if filtro_responsavel and filtro_responsavel.lower() not in (resp or "").lower():
            continue

        # Estilos pixel-perfect
        cor_fundo="#2b488e" if agenda_presidente else "#109439"
        cor_fonte="#fff" if agenda_presidente else "#0f1116"
        opacidade="1"; borda="none"; decoracao="none"; badge=""

        if status=="CANCELADO":
            decoracao="line-through"
        if data_ev<hoje or (data_ev==hoje and agora>fim_dt):
            cor_fundo="#d9d9d9"; cor_fonte="#6b6b6b"; opacidade="0.6"
        elif data_ev==hoje and inicio_dt<=agora<=fim_dt:
            borda="4px solid #ff2b2b"; badge="<span style='background:#ff2b2b;color:#fff;padding:2px 6px;border-radius:5px;font-weight:bold;'>AGORA</span>"
        elif data_ev==hoje and inicio_dt>agora:
            borda="3px solid #FFD700"; badge="<span style='background:#FFD700;color:#000;padding:2px 6px;border-radius:5px;font-weight:bold;'>HOJE</span>"
        elif data_ev==hoje and agora>fim_dt:
            borda="3px solid #FFD700"; badge="<span style='background:#FFD700;color:#000;padding:2px 6px;border-radius:5px;font-weight:bold;'>HOJE</span>"

        # Motorista com link WhatsApp
        motorista_html=""
        if precisa_m and mot_tel:
            tel=mot_tel.replace(" ","").replace("-","").replace("(","").replace(")","")
            motorista_html=f"🚗 {mot_nome} <a href='https://wa.me/{tel}' target='_blank'>{mot_tel}</a><br>"

        # Renderizar card
        st.markdown(f"""
        <div style="background:{cor_fundo};color:{cor_fonte};opacity:{opacidade};
            padding:16px;border-radius:10px;margin-bottom:10px;border:{borda};
            text-decoration:{decoracao};">
        <h3>{'👑' if agenda_presidente else '📌'} {titulo} {badge}</h3>
        📅 {data_ev.strftime('%d/%m/%Y')} | ⏰ {hi.strftime('%H:%M')} às {hf.strftime('%H:%M')}<br>
        📍 {local}<br>🏠 {endereco}<br>🎥 {cobertura}<br>👥 {resp}<br>🎒 {equip}<br>
        {motorista_html}📝 {obs}<br><b>Status:</b> {status}
        </div>
        """, unsafe_allow_html=True)

        c1,c2,c3=st.columns(3)
        if c1.button("✏️ Editar",key=f"e{id_ev}"):
            st.session_state.editando=True
            st.session_state.evento_id=id_ev
            st.experimental_rerun()
        if c2.button("❌ Cancelar/Reativar",key=f"c{id_ev}"):
            novo_status="CANCELADO" if status=="ATIVO" else "ATIVO"
            cursor.execute("UPDATE eventos SET status=%s WHERE id=%s",(novo_status,id_ev))
            conn.commit()
            st.experimental_rerun()
        if c3.button("🗑 Apagar",key=f"d{id_ev}"):
            cursor.execute("DELETE FROM eventos WHERE id=%s",(id_ev,))
            conn.commit()
            st.experimental_rerun()

# ==============================
# Execução
# ==============================
# pip install streamlit psycopg2
# streamlit run app.py
