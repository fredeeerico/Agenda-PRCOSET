import streamlit as st
import sqlite3
from datetime import date, time, datetime, timedelta, timezone
import pandas as pd

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO

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
# BANCO DE DADOS
# -----------------------------
conn = sqlite3.connect("agenda.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agenda_presidente INTEGER,
    titulo TEXT,
    data TEXT,
    hora_inicio TEXT,
    hora_fim TEXT,
    local TEXT,
    endereco TEXT,
    cobertura TEXT,
    responsaveis TEXT,
    equipamentos TEXT,
    observacoes TEXT,
    precisa_motorista INTEGER,
    motorista_nome TEXT,
    motorista_telefone TEXT,
    status TEXT
)
""")
conn.commit()

# -----------------------------
# FUNÇÕES PDF / CSV
# -----------------------------
def gerar_pdf_eventos(eventos_lista):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Agenda PRCOSET - Eventos", styles["Title"]))
    elementos.append(Spacer(1, 12))

    for ev in eventos_lista:
        (
            _, _, titulo, data_evento, hora_inicio, hora_fim,
            local, endereco, cobertura, responsaveis, equipamentos,
            observacoes, _, motorista_nome, motorista_telefone, status
        ) = ev

        texto = f"""
        <b>{titulo}</b><br/>
        📅 {data_evento} | ⏰ {hora_inicio} às {hora_fim}<br/>
        📍 {local}<br/>
        🏠 {endereco}<br/>
        🎥 {cobertura}<br/>
        👥 {responsaveis}<br/>
        🎒 {equipamentos}<br/>
        🚗 {motorista_nome or ""} {motorista_telefone or ""}<br/>
        📝 {observacoes}<br/>
        Status: {status}<br/><br/>
        """
        elementos.append(Paragraph(texto, styles["Normal"]))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

def gerar_csv(cursor):
    cursor.execute("SELECT * FROM eventos")
    dados = cursor.fetchall()

    colunas = [
        "id","agenda_presidente","titulo","data","hora_inicio","hora_fim",
        "local","endereco","cobertura","responsaveis","equipamentos",
        "observacoes","precisa_motorista","motorista_nome",
        "motorista_telefone","status"
    ]
    return pd.DataFrame(dados, columns=colunas)

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
        cursor.execute("SELECT * FROM eventos WHERE id=?", (st.session_state.evento_id,))
        evento = cursor.fetchone()
        st.warning("✏️ Você está editando um evento já existente.")

    with st.form("form_evento"):
        agenda_presidente = st.checkbox(
            "👑 Agenda do Presidente?",
            value=bool(evento[1]) if evento else False
        )

        precisa_motorista = st.checkbox(
            "🚗 Precisa de motorista?",
            value=bool(evento[12]) if evento else False
        )

        titulo = st.text_input("📝 Título", value=evento[2] if evento else "")

        col1, col2, col3 = st.columns(3)
        with col1:
            data_evento = st.date_input("📅 Data", value=date.fromisoformat(evento[3]) if evento else date.today())
        with col2:
            hora_inicio = st.time_input("⏰ Início", value=time.fromisoformat(evento[4]) if evento else time(9,0))
        with col3:
            hora_fim = st.time_input("⏰ Fim", value=time.fromisoformat(evento[5]) if evento else time(10,0))

        local = st.text_input("📍 Local", value=evento[6] if evento else "")
        endereco = st.text_input("🏠 Endereço", value=evento[7] if evento else "")

        cobertura = st.multiselect(
            "🎥 Cobertura",
            ["Redes", "Foto", "Vídeo", "Imprensa"],
            default=evento[8].split(", ") if evento and evento[8] else []
        )

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
                int(agenda_presidente), titulo, data_evento.isoformat(),
                hora_inicio.strftime("%H:%M"), hora_fim.strftime("%H:%M"),
                local, endereco, ", ".join(cobertura),
                responsaveis, equipamentos, observacoes,
                int(precisa_motorista), motorista_nome,
                motorista_telefone, status
            )

            if evento:
                cursor.execute("""
                UPDATE eventos SET
                agenda_presidente=?, titulo=?, data=?, hora_inicio=?, hora_fim=?,
                local=?, endereco=?, cobertura=?, responsaveis=?, equipamentos=?,
                observacoes=?, precisa_motorista=?, motorista_nome=?, motorista_telefone=?, status=?
                WHERE id=?
                """, dados + (st.session_state.evento_id,))
            else:
                cursor.execute("""
                INSERT INTO eventos (
                agenda_presidente,titulo,data,hora_inicio,hora_fim,
                local,endereco,cobertura,responsaveis,equipamentos,
                observacoes,precisa_motorista,motorista_nome,motorista_telefone,status
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, dados)

            conn.commit()
            st.session_state.editando = False
            st.session_state.evento_id = None
            st.session_state.aba_ativa = "📋 Eventos"
            st.rerun()

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
        ver_todos = st.toggle("🔎 Ver todos os eventos", value=False)

    cursor.execute("""
    SELECT * FROM eventos
    ORDER BY data ASC, hora_inicio ASC, hora_fim ASC, agenda_presidente DESC
    """)
    eventos = cursor.fetchall()

    hoje = date.today()
    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)

    eventos_visiveis = []

    for ev in eventos:
        data_db = datetime.strptime(ev[3], "%Y-%m-%d").date()

        if filtro_data and data_db != filtro_data:
            continue
        if filtro_agenda == "Agenda do Presidente" and not ev[1]:
            continue
        if filtro_agenda == "Outras agendas" and ev[1]:
            continue
        if filtro_responsavel and filtro_responsavel.lower() not in (ev[9] or "").lower():
            continue

        eventos_visiveis.append(ev)

    with col_lista:
        for ev in eventos_visiveis:
            (
                id_evento, agenda_presidente_db, titulo, data_evento,
                hora_inicio, hora_fim, local, endereco, cobertura,
                responsaveis, equipamentos, observacoes,
                precisa_motorista_db, motorista_nome_db,
                motorista_telefone_db, status
            ) = ev

            data_db = datetime.strptime(data_evento, "%Y-%m-%d").date()
            inicio_dt = datetime.combine(data_db, datetime.strptime(hora_inicio,"%H:%M").time())
            fim_dt = datetime.combine(data_db, datetime.strptime(hora_fim,"%H:%M").time())

            badge = ""
            borda = "none"
            opacidade = "1"

            if data_db < hoje:
                cor_fundo="#d9d9d9"; cor_fonte="#6b6b6b"; icone="📌"; opacidade="0.6"
            elif data_db==hoje and agora>fim_dt:
                cor_fundo="#d9d9d9"; cor_fonte="#6b6b6b"; icone="📌"; opacidade="0.6"
                borda="3px solid #FFD700"
                badge="<span style='padding:2px 6px;border-radius:5px;font-weight:bold;background:#FFD700;color:#000;'>HOJE</span>"
            elif data_db==hoje and inicio_dt<=agora<=fim_dt:
                cor_fundo="#2b488e" if agenda_presidente_db else "#109439"
                cor_fonte="#fff" if agenda_presidente_db else "#0f1116"
                icone="👑" if agenda_presidente_db else "📌"
                borda="4px solid #ff2b2b"
                badge="<span style='padding:2px 6px;border-radius:5px;font-weight:bold;background:#ff2b2b;color:#fff;'>AGORA</span>"
            elif data_db==hoje:
                cor_fundo="#2b488e" if agenda_presidente_db else "#109439"
                cor_fonte="#fff" if agenda_presidente_db else "#0f1116"
                icone="👑" if agenda_presidente_db else "📌"
                borda="3px solid #FFD700"
                badge="<span style='padding:2px 6px;border-radius:5px;font-weight:bold;background:#FFD700;color:#000;'>HOJE</span>"
            else:
                cor_fundo="#2b488e" if agenda_presidente_db else "#109439"
                cor_fonte="#fff" if agenda_presidente_db else "#0f1116"
                icone="👑" if agenda_presidente_db else "📌"

            decoracao = "line-through" if status=="CANCELADO" else "none"

            motorista_html=""
            if precisa_motorista_db and motorista_telefone_db:
                tel = motorista_telefone_db.replace(" ","").replace("-","").replace("(","").replace(")","")
                motorista_html = f"🚗 {motorista_nome_db} <a href='https://wa.me/{tel}' target='_blank'>{motorista_telefone_db}</a><br>"

            st.markdown(f"""
            <div style="background:{cor_fundo};color:{cor_fonte};opacity:{opacidade};
            padding:16px;border-radius:10px;margin-bottom:10px;
            border:{borda};text-decoration:{decoracao};">
            <h3>{icone} {titulo} {badge}</h3>
            📅 {data_db.strftime('%d/%m/%Y')} | ⏰ {hora_inicio} às {hora_fim}<br>
            📍 {local}<br>
            🏠 {endereco}<br>
            🎥 {cobertura}<br>
            👥 {responsaveis}<br>
            🎒 {equipamentos}<br>
            {motorista_html}
            📝 {observacoes}<br><br>
            <b>Status:</b> {status}
            </div>
            """, unsafe_allow_html=True)

            c1,c2,c3 = st.columns(3)

            if c1.button("✏️ Editar", key=f"e{id_evento}"):
                st.session_state.editando=True
                st.session_state.evento_id=id_evento
                st.session_state.aba_ativa="📝 Novo Evento"
                st.rerun()

            if c2.button("❌ Cancelar/Reativar", key=f"c{id_evento}"):
                novo="CANCELADO" if status=="ATIVO" else "ATIVO"
                cursor.execute("UPDATE eventos SET status=? WHERE id=?", (novo,id_evento))
                conn.commit()
                st.rerun()

            if c3.button("🗑 Apagar", key=f"d{id_evento}"):
                cursor.execute("DELETE FROM eventos WHERE id=?", (id_evento,))
                conn.commit()
                st.rerun()
