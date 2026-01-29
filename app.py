import streamlit as st
import psycopg2
from datetime import datetime, date, time, timedelta, timezone

# -----------------------------
# 1. CONEXÃO E LIMPEZA
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
conn.rollback() 

# -----------------------------
# 2. ESTADOS E CONFIGURAÇÃO
# -----------------------------
st.set_page_config(page_title="Agenda PRCOSET", page_icon="📅", layout="wide")

for key in ["aba_atual", "editando", "evento_id", "msg"]:
    if key not in st.session_state:
        st.session_state[key] = "LISTA" if key == "aba_atual" else None

st.title("📅 Agenda PRCOSET")

# Menu Superior
cm1, cm2, _ = st.columns([1, 1, 4])
if cm1.button("📋 Ver Lista", use_container_width=True):
    st.session_state.aba_atual = "LISTA"
    st.rerun()
if cm2.button("➕ Novo Evento", use_container_width=True):
    st.session_state.aba_atual = "FORM"
    st.session_state.editando, st.session_state.evento_id = False, None
    st.rerun()

st.markdown("---")

if st.session_state.msg:
    st.success(st.session_state.msg)
    st.session_state.msg = None

# -----------------------------
# 3. TELA DE FORMULÁRIO
# -----------------------------
if st.session_state.aba_atual == "FORM":
    ev_db = None
    if st.session_state.editando and st.session_state.evento_id:
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (st.session_state.evento_id,))
        ev_db = cursor.fetchone()

    with st.form("form_evento"):
        st.subheader("📝 Detalhes do Evento")
        
        c_t1, c_t2 = st.columns(2)
        pres_val = c_t1.checkbox("👑 Agenda Presidente?", value=bool(ev_db[1]) if ev_db else False)
        mot_val = c_t2.checkbox("🚗 Precisa Motorista?", value=bool(ev_db[12]) if ev_db else False)
        
        tit_val = st.text_input("📝 Título", value=str(ev_db[2]) if ev_db else "")
        
        c = st.columns(3)
        data_val = c[0].date_input("📅 Data", value=ev_db[3] if ev_db else date.today())
        hi_val = c[1].time_input("⏰ Início", value=ev_db[4] if ev_db else time(9,0))
        hf_val = c[2].time_input("⏰ Fim", value=ev_db[5] if ev_db else time(10,0))

        loc_val = st.text_input("📍 Local", value=str(ev_db[6]) if ev_db else "")
        end_val = st.text_input("🏠 Endereço", value=str(ev_db[7]) if ev_db else "")
        
        cob_opcoes = ["Redes", "Foto", "Vídeo", "Imprensa"]
        cob_def = str(ev_db[8]).split(", ") if ev_db and ev_db[8] else []
        cob_val = st.multiselect("🎥 Cobertura", cob_opcoes, default=[c for c in cob_def if c in cob_opcoes])
        
        resp_val = st.text_input("👥 Responsáveis", value=str(ev_db[9]) if ev_db else "")
        eq_val = st.text_input("🎒 Equipamentos", value=str(ev_db[10]) if ev_db else "")
        obs_val = st.text_area("📝 Observações", value=str(ev_db[11]) if ev_db else "")
        
        cmot1, cmot2 = st.columns(2)
        nm_val = cmot1.text_input("Nome Motorista", value=str(ev_db[13]) if ev_db else "")
        tm_val = cmot2.text_input("Tel Motorista", value=str(ev_db[14]) if ev_db else "")
        
        st_val = st.selectbox("Status", ["ATIVO", "CANCELADO"], index=0 if not ev_db or ev_db[15]=="ATIVO" else 1)

        salvar = st.form_submit_button("💾 SALVAR EVENTO", use_container_width=True)

        if salvar:
            dados = (
                1 if pres_val else 0, tit_val, data_val, hi_val, hf_val,
                loc_val, end_val, ", ".join(cob_val), resp_val, eq_val,
                obs_val, 1 if mot_val else 0, nm_val, tm_val, st_val
            )
            try:
                if st.session_state.editando:
                    cursor.execute("""UPDATE eventos SET agenda_presidente=%s, titulo=%s, data=%s, hora_inicio=%s, hora_fim=%s, 
                        local=%s, endereco=%s, cobertura=%s, responsaveis=%s, equipamentos=%s, observacoes=%s, 
                        precisa_motorista=%s, motorista_nome=%s, motorista_telefone=%s, status=%s WHERE id=%s""", 
                        dados + (st.session_state.evento_id,))
                else:
                    cursor.execute("""INSERT INTO eventos (agenda_presidente, titulo, data, hora_inicio, hora_fim, local, endereco, 
                        cobertura, responsaveis, equipamentos, observacoes, precisa_motorista, motorista_nome, motorista_telefone, status) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", dados)
                conn.commit()
                st.session_state.aba_atual, st.session_state.msg = "LISTA", "💾 Evento salvo com sucesso!"
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"Erro ao salvar: {e}")

# -----------------------------
# 4. TELA DE LISTAGEM (BORDAS CORRIGIDAS)
# -----------------------------
elif st.session_state.aba_atual == "LISTA":
    
    with st.expander("🔍 FILTRAR BUSCA", expanded=False):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1: filtro_data = st.date_input("Filtrar por Data", value=None)
        with f_col2: filtro_tipo = st.selectbox("Tipo de Agenda", ["Todas", "Agenda do Presidente", "Outras Agendas"])
        with f_col3: filtro_equipe = st.text_input("Buscar por Responsável", placeholder="Ex: Fred, Ana...")

    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC")
    eventos = cursor.fetchall()
    
    agora_dt = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)
    hoje = agora_dt.date()
    hora_agora_str = agora_dt.time().strftime('%H:%M')

    def formatar_hora(valor):
        if isinstance(valor, time):
            return valor.strftime('%H:%M')
        try:
            return str(valor)[:5]
        except:
            return "00:00"

    if not eventos:
        st.info("Nenhum evento encontrado.")

    for ev in eventos:
        d_dt = ev[3] if isinstance(ev[3], date) else datetime.strptime(str(ev[3]), "%Y-%m-%d").date()

        if filtro_data and d_dt != filtro_data: continue
        if filtro_tipo == "Agenda do Presidente" and ev[1] != 1: continue
        if filtro_tipo == "Outras Agendas" and ev[1] == 1: continue
        if filtro_equipe and filtro_equipe.lower() not in str(ev[9]).lower(): continue

        # --- LÓGICA DE CORES E BORDAS ---
        cor_base = "#2b488e" if ev[1] == 1 else "#109439"
        cor_fonte = "white"
        borda_4_lados = "1px solid rgba(255,255,255,0.2)" # Borda padrão sutil
        barra_esquerda = "12px solid #ffffff44" # Barra padrão
        badge, opac = "", "1"
        decor = "line-through" if ev[15] == "CANCELADO" else "none"

        if d_dt < hoje:
            cor_base, cor_fonte, opac = "#d9d9d9", "#666666", "0.7"
            barra_esquerda = "12px solid #999999"
        
        elif d_dt == hoje:
            # HOJE: Borda 4 lados amarela + Barra esquerda amarela
            borda_4_lados = "4px solid #FFD700"
            barra_esquerda = "12px solid #FFD700"
            badge = "<span style='background:#FFD700; color:black; padding:3px 10px; border-radius:10px; font-weight:bold; font-size:12px; margin-left:10px;'>HOJE!</span>"
            
            hi_s = formatar_hora(ev[4])
            hf_s = formatar_hora(ev[5])
            if hi_s <= hora_agora_str <= hf_s:
                # AGORA: Borda 4 lados vermelha + Barra esquerda vermelha
                borda_4_lados = "4px solid #ff2b2b"
                barra_esquerda = "12px solid #ff2b2b"
                badge = "<span style='background:#ff2b2b; color:white; padding:3px 10px; border-radius:10px; font-weight:bold; font-size:12px; margin-left:10px;'>AGORA!</span>"

        link_zap = ""
        if ev[12] == 1 and ev[14]:
            zap_limpo = "".join(filter(str.isdigit, str(ev[14])))
            link_zap = f"<br>🚗 <b>Motorista:</b> {ev[13]} (<a href='https://wa.me{zap_limpo}' style='color:{cor_fonte}; font-weight:bold;'>{ev[14]}</a>)"

        # --- RENDERIZAÇÃO ---
        st.markdown(f"""
        <div style="background:{cor_base}; color:{cor_fonte}; padding:22px; border-radius:15px; margin-bottom:15px; 
                    opacity:{opac}; text-decoration:{decor}; 
                    border:{borda_4_lados}; border-left:{barra_esquerda};">
            <h3 style="margin:0; font-size:22px;">{'👑' if ev[1] == 1 else '📌'} {ev[2]} {badge} 
                <span style="float:right; font-size:12px; background:rgba(0,0,0,0.3); padding:5px 12px; border-radius:20px;">{ev[15]}</span>
            </h3>
            <div style="margin-top:12px; font-size:16px; line-height:1.6;">
                <b>📅 {d_dt.strftime('%d/%m/%Y')}</b> | ⏰ {formatar_hora(ev[4])} às {formatar_hora(ev[5])}<br>
                📍 <b>Local:</b> {ev[6]}<br>
                🏠 <b>Endereço:</b> {ev[7]}<br>
                🎥 <b>Cobertura:</b> {ev[8]} | 👥 <b>Equipe:</b> {ev[9]}<br>
                🎒 <b>Equipamentos:</b> {ev[10]} {link_zap}
            </div>
            <div style="background: rgba(255,255,255,0.15); padding: 12px; border-radius: 8px; margin-top: 15px; font-size:14px; border: 1px dashed rgba(255,255,255,0.3);">
                <b>📝 OBSERVAÇÕES:</b> {ev[11] if ev[11] else "Sem observações."}
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, _ = st.columns([1, 1.2, 1, 4])
        with c1:
            if st.button("✏️ Editar", key=f"e_{ev[0]}"):
                st.session_state.editando, st.session_state.evento_id, st.session_state.aba_atual = True, ev[0], "FORM"
                st.rerun()
        with c2:
            novo_st = "CANCELADO" if ev[15]=="ATIVO" else "ATIVO"
            if st.button(f"🚫 Status", key=f"s_{ev[0]}"):
                cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", (novo_st, ev[0]))
                conn.commit(); st.rerun()
        with c3:
            if st.button("🗑️ Excluir", key=f"d_{ev[0]}"):
                cursor.execute("DELETE FROM eventos WHERE id=%s", (ev[0],))
                conn.commit(); st.rerun()

# -----------------------------
# 5. TELA DE LISTAGEM (CARDS COMPLETOS)
# -----------------------------
elif st.session_state.aba_atual == "LISTA":
    cursor.execute("SELECT * FROM eventos ORDER BY data ASC, hora_inicio ASC")
    eventos = cursor.fetchall()
    agora = datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)

    if not eventos:
        st.info("Nenhum evento encontrado.")

    for ev in eventos:
        # MAPEAMENTO: 0:id, 1:pres, 2:tit, 3:data, 4:hi, 5:hf, 6:loc, 7:end, 8:cob, 9:resp, 10:eq, 11:obs, 12:pmot, 13:nmot, 14:tmot, 15:stat
        d_dt = ev[3] if isinstance(ev[3], date) else datetime.strptime(str(ev[3]), "%Y-%m-%d").date()
        cor = "#2b488e" if ev[1] == 1 else "#109439"
        opac = "0.6" if d_dt < agora.date() else "1"
        decor = "line-through" if ev[15] == "CANCELADO" else "none"
        
        # Link WhatsApp Motorista
        link_zap = ""
        if ev[12] == 1 and ev[14]:
            zap_limpo = "".join(filter(str.isdigit, str(ev[14])))
            link_zap = f"<br>🚗 <b>Motorista:</b> {ev[13]} (<a href='https://wa.me{zap_limpo}' style='color:white; font-weight:bold;'>{ev[14]}</a>)"

        st.markdown(f"""
        <div style="background:{cor}; color:white; padding:22px; border-radius:15px; margin-bottom:15px; opacity:{opac}; text-decoration:{decor}; border-left: 12px solid {'#FFD700' if ev[1] == 1 else '#ffffff44'};">
            <h3 style="margin:0; font-size:22px;">{'👑' if ev[1] == 1 else '📌'} {ev[2]} <span style="float:right; font-size:12px; background:rgba(0,0,0,0.3); padding:5px 12px; border-radius:20px;">{ev[15]}</span></h3>
            <div style="margin-top:12px; font-size:16px; line-height:1.6;">
                <b>📅 {d_dt.strftime('%d/%m/%Y')}</b> | ⏰ {ev[4]} às {ev[5]}<br>
                📍 <b>Local:</b> {ev[6]}<br>
                🏠 <b>Endereço:</b> {ev[7]}<br>
                🎥 <b>Cobertura:</b> {ev[8]} | 👥 <b>Equipe:</b> {ev[9]}<br>
                🎒 <b>Equipamentos:</b> {ev[10]} {link_zap}
            </div>
            <div style="background: rgba(255,255,255,0.15); padding: 12px; border-radius: 8px; margin-top: 15px; font-size:14px; border: 1px dashed rgba(255,255,255,0.3);">
                <b>📝 OBSERVAÇÕES:</b> {ev[11] if ev[11] else "Sem observações."}
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, _ = st.columns([1, 1.2, 1, 4])
        if c1.button("✏️ Editar", key=f"e_{ev[0]}"):
            st.session_state.editando, st.session_state.evento_id, st.session_state.aba_atual = True, ev[0], "FORM"
            st.rerun()
        if c2.button("🚫 Alterar Status", key=f"s_{ev[0]}"):
            novo_s = "CANCELADO" if ev[15]=="ATIVO" else "ATIVO"
            cursor.execute("UPDATE eventos SET status=%s WHERE id=%s", (novo_s, ev[0]))
            conn.commit(); st.rerun()
        if c3.button("🗑️ Excluir", key=f"d_{ev[0]}"):
            cursor.execute("DELETE FROM eventos WHERE id=%s", (ev[0],))
            conn.commit(); st.rerun()






