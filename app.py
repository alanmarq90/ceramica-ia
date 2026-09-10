# ============================================================
# CERÂMICAIÁ v4.0 — Módulo de Gestão de Barros e Rastreabilidade
# ============================================================

import streamlit as st
import joblib
import pandas as pd
import numpy as np
import io
import urllib.parse
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="CerâmicaIA — Gestão de Barros e Misturas",
    page_icon="🧱",
    layout="wide"
)

# Estilização
st.markdown("""
    <style>
    .main-header {font-size: 28px; font-weight: bold; color: #b23b00;}
    .sub-header {font-size: 16px; color: #555555;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🧱 CerâmicaIA — Otimizador de Misturas e Rastreabilidade</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Previsão em tempo real, gestão de barros por jazida e cálculo financeiro de perdas</div>', unsafe_allow_html=True)
st.divider()

# 1. CATALOGO DE BARROS INICIAIS (SUAS JAZIDAS E LOCALIDADES)
BARROS_INICIAIS = [
    {
        "codigo": "01_BR_ARG_PRETO_SV",
        "nome": "Barro Argiloso Preto (São Vicente)",
        "tipo_base": "Preto",
        "localidade": "São Vicente (SV)",
        "status": "Ativo"
    },
    {
        "codigo": "02_BR_ARG_VERM_STPREZ",
        "nome": "Barro Argiloso Vermelho (Sítio Prazeres)",
        "tipo_base": "Preto",
        "localidade": "Sítio Prazeres (STPRAZ)",
        "status": "Ativo"
    },
    {
        "codigo": "03_BR_AREN_BRANCO_STPRAZ",
        "nome": "Barro Arenoso Branco (Sítio Prazeres)",
        "tipo_base": "Branco",
        "localidade": "Sítio Prazeres (STPRAZ)",
        "status": "Ativo"
    }
]

# Inicializar Catálogo de Barros em Memória (st.session_state)
if 'catalogo_barros' not in st.session_state:
    st.session_state.catalogo_barros = pd.DataFrame(BARROS_INICIAIS)

# 2. BASE HISTÓRICA INICIAL COM CÓDIGOS DE BARROS
HISTORICO_BASE_CSV = """data,modo,cod_barro_preto,cod_barro_amarelo,cod_barro_branco,preto_a,amarelo_a,branco_a,preto_b,amarelo_b,branco_b,pct_preto,pct_amarelo,pct_branco,umidade,residuo,retracao,esp_parede,peso,comprimento,tipo_bloco,class_residuo,excesso_peso,observacoes
2025-03-20,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,17.0,33.7,3,0.90,3.600,20.4,01-BLP,fraco,800,Histórico inicial
2025-03-21,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,17.0,32.0,3,0.85,3.185,20.5,01-BLP,limite,385,Histórico inicial
2025-03-24,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,10.0,28.0,3,0.82,3.100,20.7,01-BLP,ideal,300,Histórico inicial
2025-03-25,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,15.0,29.0,3,0.80,3.125,20.5,01-BLP,ideal,325,Histórico inicial
2025-03-27,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,16.0,31.5,3,0.85,3.184,20.5,01-BLP,ideal,384,Histórico inicial
2025-03-28,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,16.0,28.7,3,0.77,3.074,20.0,01-BLP,ideal,274,Histórico inicial
2025-04-02,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,14.0,29.2,4,0.80,3.244,20.7,01-BLP,ideal,444,Histórico inicial
2025-04-03,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,16.0,30.0,3,0.87,3.114,20.2,01-BLP,ideal,314,Histórico inicial
2025-04-09,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,15.0,30.9,4,0.82,3.231,20.0,01-BLP,ideal,431,Histórico inicial
2025-04-10,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,14.0,33.5,4,0.90,3.237,20.0,01-BLP,fraco,437,Histórico inicial
2025-08-18,Unica,02_BR_ARG_VERM_STPREZ,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,14.0,32.0,4,0.675,3.020,20.1,01-BLP,limite,220,Histórico Clessinho / Prazeres
2025-08-19,Unica,02_BR_ARG_VERM_STPREZ,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,11.0,31.0,3,0.675,3.000,20.0,01-BLP,ideal,200,Histórico Clessinho / Prazeres
2025-08-21,Unica,02_BR_ARG_VERM_STPREZ,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,13.0,34.0,3,0.65,3.048,20.3,01-BLP,fraco,248,Histórico Clessinho / Prazeres
2026-09-02,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,1,1,3,1,2,0.550,0.183,0.267,17.0,30.0,3,0.68,2.935,20.3,01-BLP,ideal,135,Histórico recente 3 barros
2026-09-08,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,1,1,3,1,2,0.550,0.183,0.267,17.8,31.3,3,0.65,2.990,20.4,01-BLP,ideal,190,Histórico recente 3 barros"""

if 'df_master' not in st.session_state:
    st.session_state.df_master = pd.read_csv(io.StringIO(HISTORICO_BASE_CSV))

if 'diagnostico_gerado' not in st.session_state:
    st.session_state.diagnostico_gerado = False

# Carregar Modelos Treinados
@st.cache_resource
def carregar_modelos():
    m_res = joblib.load('modelo_residuo.pkl')
    m_ret = joblib.load('modelo_retracao.pkl')
    m_pes = joblib.load('modelo_peso.pkl')
    return m_res, m_ret, m_pes

try:
    m_res, m_ret, m_pes = carregar_modelos()
except Exception as e:
    st.error(f"Erro ao carregar os arquivos de modelo .pkl: {e}")
    st.stop()

# CATALOGO DE PRODUTOS
CATALOGO_PRODUTOS = {
    "01-BLP (9x19x19 cm) — Vedação Padrão": {"largura": 9, "comprimento": 19, "peso_padrao": 2.800, "codigo": "01-BLP"},
    "BP14 (14x19x19 cm) — Estrutural Curto": {"largura": 14, "comprimento": 19, "peso_padrao": 3.800, "codigo": "BP14"},
    "02-BLG (9x19x39 cm) — Bloco Grande / Canaleta 9": {"largura": 9, "comprimento": 39, "peso_padrao": 5.500, "codigo": "02-BLG"},
    "BG14 (14x19x39 cm) — Estrutural Grande 14": {"largura": 14, "comprimento": 39, "peso_padrao": 7.000, "codigo": "BG14"},
}

# CRIAR ABAS PRINCIPAIS DO SISTEMA
tab_diag, tab_reg, tab_barros = st.tabs([
    "🔮 Diagnóstico & Previsão", 
    "📝 Registrar Análise Real (Alimentar IA)",
    "🧱 Cadastrar / Gerenciar Barros"
])

# ============================================================
# ABA 1: DIAGNÓSTICO E PREVISÃO
# ============================================================
with tab_diag:
    st.sidebar.header("⚙️ Configurações do Lote")

    produto_sel = st.sidebar.selectbox(
        "Selecione o Produto em Produção:",
        list(CATALOGO_PRODUTOS.keys())
    )

    dados_prod = CATALOGO_PRODUTOS[produto_sel]
    largura_cm = dados_prod["largura"]
    comprimento_cm = dados_prod["comprimento"]
    peso_padrao = dados_prod["peso_padrao"]
    codigo_prod = dados_prod["codigo"]

    st.sidebar.info(f"**Meta de Peso Padrão:** {peso_padrao:.3f} kg\n\n**Dimensão:** {largura_cm}x19x{comprimento_cm} cm")

    # SELEÇÃO DOS BARROS CADASTRADOS PARA A MISTURA
    st.header("🧱 Seleção dos Barros Cadastrados")
    
    df_barros_ativos = st.session_state.catalogo_barros[st.session_state.catalogo_barros['status'] == 'Ativo']
    
    barros_pretos = df_barros_ativos[df_barros_ativos['tipo_base'] == 'Preto']['codigo'].tolist()
    barros_amarelos = ["Nenhum"] + df_barros_ativos[df_barros_ativos['tipo_base'] == 'Amarelo']['codigo'].tolist()
    barros_brancos = ["Nenhum"] + df_barros_ativos[df_barros_ativos['tipo_base'] == 'Branco']['codigo'].tolist()
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        sel_barro_preto = st.selectbox("Barro Argiloso (Forte):", barros_pretos if barros_pretos else ["01_BR_ARG_PRETO_SV"])
    with col_b2:
        sel_barro_amarelo = st.selectbox("Barro Intermediário (Médio):", barros_amarelos)
    with col_b3:
        sel_barro_branco = st.selectbox("Barro Arenoso (Fraco):", barros_brancos if len(barros_brancos)>1 else ["03_BR_AREN_BRANCO_STPRAZ"])

    st.divider()
    st.header("🏗️ Composição em Conchas")

    modo = st.radio("Tipo de Produção do Dia:", ["Receita Única", "Mistura Mesclada (Alternada)"], horizontal=True)

    if modo == "Receita Única":
        c1, c2, c3 = st.columns(3)
        with c1: preto_a = st.number_input("Conchas de Preto", 0, 10, 4, 1)
        with c2: amarelo_a = st.number_input("Conchas de Amarelo", 0, 10, 0 if sel_barro_amarelo=="Nenhum" else 1, 1)
        with c3: branco_a = st.number_input("Conchas de Branco", 0, 10, 1 if sel_barro_branco!="Nenhum" else 0, 1)
        
        preto_b, amarelo_b, branco_b = preto_a, amarelo_a, branco_a
        tot_a = max(1, preto_a + amarelo_a + branco_a)
        pct_preto = preto_a / tot_a
        pct_amarelo = amarelo_a / tot_a
        pct_branco = branco_a / tot_a
        mistura_desc = f"{preto_a}x{amarelo_a}x{branco_a}" if amarelo_a > 0 else f"{preto_a}x{branco_a}"

    else: # Mistura Mesclada
        st.subheader("Receita A")
        c1, c2, c3 = st.columns(3)
        with c1: preto_a = st.number_input("Preto (A)", 0, 10, 4, 1)
        with c2: amarelo_a = st.number_input("Amarelo (A)", 0, 10, 0, 1)
        with c3: branco_a = st.number_input("Branco (A)", 0, 10, 1, 1)
        
        st.subheader("Receita B")
        c4, c5, c6 = st.columns(3)
        with c4: preto_b = st.number_input("Preto (B)", 0, 10, 4, 1)
        with c5: amarelo_b = st.number_input("Amarelo (B)", 0, 10, 0, 1)
        with c6: branco_b = st.number_input("Branco (B)", 0, 10, 2, 1)
        
        tot_a = max(1, preto_a + amarelo_a + branco_a)
        tot_b = max(1, preto_b + amarelo_b + branco_b)
        
        pct_preto = ((preto_a / tot_a) + (preto_b / tot_b)) / 2
        pct_amarelo = ((amarelo_a / tot_a) + (amarelo_b / tot_b)) / 2
        pct_branco = ((branco_a / tot_a) + (branco_b / tot_b)) / 2
        mistura_desc = f"Mesclada ({preto_a}x{branco_a} e {preto_b}x{branco_b})"

    st.caption(f"📊 **Massa Resultante na Maromba:** {pct_preto*100:.1f}% Argiloso | {pct_amarelo*100:.1f}% Médio | {pct_branco*100:.1f}% Arenoso")

    st.divider()
    st.header("🔬 Parâmetros do Processo")

    col_u, col_e = st.columns(2)
    with col_u:
        umidade = st.number_input("Umidade do Barro (%)", 5.0, 30.0, 16.0, 0.5)
    with col_e:
        esp_parede = st.number_input("Espessura da Parede (cm)", 0.20, 1.50, 0.65, 0.01)

    st.divider()

    if st.button("🔮 GERAR DIAGNÓSTICO DO LOTE", type="primary", use_container_width=True):
        st.session_state.diagnostico_gerado = True

    if st.session_state.diagnostico_gerado:
        X_input = pd.DataFrame([{
            'pct_preto': pct_preto,
            'pct_amarelo': pct_amarelo,
            'pct_branco': pct_branco,
            'umidade': umidade,
            'esp_parede': esp_parede,
            'largura_cm': largura_cm,
            'comprimento_cm': comprimento_cm
        }])
        
        pred_res = m_res.predict(X_input)[0]
        pred_ret = m_ret.predict(X_input)[0]
        pred_pes = m_pes.predict(X_input)[0]
        
        st.header("📊 Resultados Previstos pela IA")
        
        res1, res2, res3 = st.columns(3)
        
        with res1:
            st.metric("Resíduo Previsto", f"{pred_res:.1f}%")
            if pred_res > 32.0:
                class_res, msg_res = "🔴 BLOCO FRACO / QUEBRADIÇO", "Resíduo acima de 32%. Aumente o barro Preto ou reduza o Branco."
                st.error(class_res)
            elif pred_res < 28.0:
                class_res, msg_res = "🔴 FORTE DEMAIS / RISCO TRINCA", "Resíduo abaixo de 28%. Adicione mais barro Branco."
                st.warning(class_res)
            else:
                class_res, msg_res = "🟢 FAIXA IDEAL (28% a 32%)", "Excelente resistência e equilíbrio plástico."
                st.success(class_res)
            st.caption(msg_res)
                
        with res2:
            st.metric("Retração Prevista", f"{pred_ret:.1f}%")
            if pred_ret > 4.5:
                st.warning("⚡ Retração Elevada (Atenção no secador)")
            else:
                st.success("✅ Retração Sob Controle")
                
        excesso_g = (pred_pes - peso_padrao) * 1000
        with res3:
            st.metric("Peso Previsto", f"{pred_pes:.3f} kg", delta=f"{excesso_g:+.0f}g vs Padrão", delta_color="inverse")
            if excesso_g > 50:
                st.error("⚠️ ACIMA DO PADRÃO")
            elif excesso_g < -50:
                st.warning("⚠️ ABAIXO DO PADRÃO (Risco Estrutural)")
            else:
                st.success("✅ DENTRO DO PESO PADRÃO")
                
        # CALCULADORA FINANCEIRA DE PERDAS
        texto_fin_wa = ""
        if excesso_g > 0:
            st.divider()
            st.subheader("💸 Impacto Financeiro (Excesso de Massa)")
            
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                prod_dia = st.number_input("Produção Planejada do Dia (blocos):", 1000, 200000, 50000, 5000)
            with c_p2:
                custo_barro = st.number_input("Custo da Tonelada do Barro (R$/ton):", 10.0, 200.0, 50.0, 5.0)
                
            ton_perdidas_dia = (excesso_g / 1000 * prod_dia) / 1000
            prejuizo_dia = ton_perdidas_dia * custo_barro
            prejuizo_mes = prejuizo_dia * 25
            
            st.error(f"""
                🚨 **Alerta de Perda de Matéria-Prima:**
                - **Desperdício de Massa:** {ton_perdidas_dia:.2f} toneladas de barro/dia
                - **Prejuízo Estimado no Dia:** R$ {prejuizo_dia:,.2f}
                - **Impacto Estimado no Mês (25 dias):** R$ {prejuizo_mes:,.2f}
            """)
            texto_fin_wa = f"\n💸 *PREJUÍZO EST.:* R$ {prejuizo_dia:,.0f}/dia ({ton_perdidas_dia:.1f} ton desperdiçadas)"

        # BOTÃO COMPARTILHAR WHATSAPP COM CÓDIGOS DE BARRO
        st.divider()
        msg_wa_diag = f"""🧱 *CerâmicaIA — Diagnóstico de Mistura*
        
📌 *Produto:* {codigo_prod} ({largura_cm}x19x{comprimento_cm}cm)
🧱 *Barro Argiloso:* {sel_barro_preto}
🧱 *Barro Arenoso:* {sel_barro_branco}
📊 *Mistura:* {mistura_desc} | 💧 *Umid:* {umidade}% | 📏 *Esp:* {esp_parede}cm

📊 *PREVISÃO DA IA:*
• *Resíduo:* {pred_res:.1f}% ({class_res})
• *Retração:* {pred_ret:.1f}%
• *Peso Est.:* {pred_pes:.3f} kg ({excesso_g:+.0f}g vs Meta){texto_fin_wa}

💡 *Gerado pelo CerâmicaIA App*"""

        wa_url_diag = f"https://wa.me/?text={urllib.parse.quote(msg_wa_diag)}"
        st.link_button("📲 Compartilhar Diagnóstico no WhatsApp", wa_url_diag, type="secondary", use_container_width=True)

# ============================================================
# ABA 2: REGISTRAR ANÁLISE REAL (ALIMENTAR A IA)
# ============================================================
with tab_reg:
    st.header("📝 Registrar Análise de Laboratório Real")
    st.caption("Alimente o sistema com os dados reais medidos para enriquecer a Rastreabilidade da fábrica.")
    
    df_barros_ativos_reg = st.session_state.catalogo_barros[st.session_state.catalogo_barros['status'] == 'Ativo']
    barros_pretos_reg = df_barros_ativos_reg[df_barros_ativos_reg['tipo_base'] == 'Preto']['codigo'].tolist()
    barros_amarelos_reg = ["Nenhum"] + df_barros_ativos_reg[df_barros_ativos_reg['tipo_base'] == 'Amarelo']['codigo'].tolist()
    barros_brancos_reg = ["Nenhum"] + df_barros_ativos_reg[df_barros_ativos_reg['tipo_base'] == 'Branco']['codigo'].tolist()

    with st.form("form_registro_lote", clear_on_submit=True):
        st.subheader("1. Identificação e Barro Utilizado")
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            data_lote = st.date_input("Data do Teste", datetime.now())
            prod_lote = st.selectbox("Produto Testado", list(CATALOGO_PRODUTOS.keys()))
            codigo_selecionado = CATALOGO_PRODUTOS[prod_lote]["codigo"]
            comprimento_selecionado = CATALOGO_PRODUTOS[prod_lote]["comprimento"]
        with f_col2:
            cod_p_reg = st.selectbox("Código Barro Preto:", barros_pretos_reg if barros_pretos_reg else ["01_BR_ARG_PRETO_SV"])
            cod_a_reg = st.selectbox("Código Barro Amarelo:", barros_amarelos_reg)
            cod_b_reg = st.selectbox("Código Barro Branco:", barros_brancos_reg if len(barros_brancos_reg)>1 else ["03_BR_AREN_BRANCO_STPRAZ"])
        with f_col3:
            modo_lote = st.selectbox("Tipo de Produção", ["Unica", "Mesclada"])

        st.subheader("2. Quantidade de Conchas")
        f_con1, f_con2 = st.columns(2)
        with f_con1:
            st.caption("Receita A")
            p_a = st.number_input("Preto A", 0, 10, 4)
            a_a = st.number_input("Amarelo A", 0, 10, 0)
            b_a = st.number_input("Branco A", 0, 10, 1)
        with f_con2:
            st.caption("Receita B (se mesclada)")
            p_b = st.number_input("Preto B", 0, 10, p_a)
            a_b = st.number_input("Amarelo B", 0, 10, a_a)
            b_b = st.number_input("Branco B", 0, 10, b_a)

        st.subheader("3. Medições do Laboratório")
        f_col4, f_col5, f_col6, f_col7 = st.columns(4)
        with f_col4: umidade_real = st.number_input("Umidade Real (%)", 0.0, 40.0, 16.0, 0.1)
        with f_col5: residuo_real = st.number_input("Resíduo Real (%)", 0.0, 50.0, 30.0, 0.1)
        with f_col6: retracao_real = st.number_input("Retração Real (%)", 0.0, 10.0, 3.0, 0.1)
        with f_col7: esp_real = st.number_input("Espessura Parede (cm)", 0.0, 2.0, 0.65, 0.01)

        f_col8, f_col9 = st.columns(2)
        with f_col8: peso_real = st.number_input("Peso Real Medido (kg)", 0.0, 15.0, 3.100, 0.001)
        with f_col9: obs_texto = st.text_area("💬 Observações (ex: 'jazida nova', 'trocou fita maromba'):", "Teste de rotina")
        
        btn_salvar = st.form_submit_button("💾 Salvar Registro e Unificar Base", type="primary", use_container_width=True)
        
        if btn_salvar:
            tot_a_l = max(1, p_a + a_a + b_a)
            tot_b_l = max(1, p_b + a_b + b_b)
            pct_p_l = ((p_a / tot_a_l) + (p_b / tot_b_l)) / 2
            pct_a_l = ((a_a / tot_a_l) + (a_b / tot_b_l)) / 2
            pct_b_l = ((b_a / tot_a_l) + (b_b / tot_b_l)) / 2
            
            class_res_l = "fraco" if residuo_real > 32 else ("forte" if residuo_real < 28 else "ideal")
            peso_meta_l = CATALOGO_PRODUTOS[prod_lote]["peso_padrao"]
            excesso_l = (peso_real - peso_meta_l) * 1000
            
            novo_row = {
                "data": data_lote.strftime("%Y-%m-%d"),
                "modo": modo_lote,
                "cod_barro_preto": cod_p_reg,
                "cod_barro_amarelo": cod_a_reg,
                "cod_barro_branco": cod_b_reg,
                "preto_a": p_a, "amarelo_a": a_a, "branco_a": b_a,
                "preto_b": p_b, "amarelo_b": a_b, "branco_b": b_b,
                "pct_preto": round(pct_p_l, 3), "pct_amarelo": round(pct_a_l, 3), "pct_branco": round(pct_b_l, 3),
                "umidade": umidade_real, "residuo": residuo_real, "retracao": retracao_real,
                "esp_parede": esp_real, "peso": peso_real, "comprimento": comprimento_selecionado,
                "tipo_bloco": codigo_selecionado, "class_residuo": class_res_l, "excesso_peso": round(excesso_l, 0),
                "observacoes": obs_texto
            }
            
            st.session_state.df_master = pd.concat([pd.DataFrame([novo_row]), st.session_state.df_master], ignore_index=True)
            st.success("✅ Lote registrado com sucesso! A base completa foi atualizada com o Código do Barro.")

            msg_wa_reg = f"""📝 *CerâmicaIA — Registro de Lab Real*
            
📌 *Data:* {data_lote.strftime('%d/%m/%Y')} | *Produto:* {codigo_selecionado}
🧱 *Barro Preto:* {cod_p_reg}
🧱 *Barro Branco:* {cod_b_reg}
🧪 *MENSURAÇÕES REAIS:*
• *Resíduo:* {residuo_real}% ({class_res_l.upper()})
• *Umidade:* {umidade_real}% | *Retração:* {retracao_real}%
• *Peso Real:* {peso_real:.3f} kg ({excesso_l:+.0f}g vs meta)
• *Espessura:* {esp_real} cm

💬 *Obs:* {obs_texto}"""

            wa_url_reg = f"https://wa.me/?text={urllib.parse.quote(msg_wa_reg)}"
            st.link_button("📲 Compartilhar Teste de Lab no WhatsApp", wa_url_reg)

    st.divider()
    st.subheader(f"📋 Base de Dados Completa da Fábrica ({len(st.session_state.df_master)} Lotes Totais)")
    st.dataframe(st.session_state.df_master, use_container_width=True)
    
    csv_completo = st.session_state.df_master.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 BAIXAR PLANILHA COMPLETA ATUALIZADA PARA RE-TREINO NA IA (CSV)",
        data=csv_completo,
        file_name=f"ceramica_lotes_completo_para_colab_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True
    )

# ============================================================
# ABA 3: CADASTRO E GESTÃO DE BARROS / JAZIDAS
# ============================================================
with tab_barros:
    st.header("🧱 Cadastro e Controle de Barros / Jazidas")
    st.caption("Cadastre novas jazidas e barros para habilitar a seleção no chão de fábrica e enriquecer o aprendizado da IA.")
    
    col_cad1, col_cad2 = st.columns([1, 2])
    
    with col_cad1:
        st.subheader("➕ Cadastrar Novo Barro")
        with st.form("form_novo_barro", clear_on_submit=True):
            novo_cod = st.text_input("Código Oficial (ex: 04_BR_ARG_PRETO_JAZIDA2):")
            novo_nome = st.text_input("Nome / Apelido Comercial:")
            novo_tipo = st.selectbox("Tipo Base para IA:", ["Preto", "Amarelo", "Branco"])
            nova_loc = st.text_input("Localidade / Jazida (ex: São Vicente, Sítio Prazeres):")
            
            btn_cad_barro = st.form_submit_button("🧱 Cadastrar Barro", type="primary", use_container_width=True)
            
            if btn_cad_barro:
                if novo_cod and novo_nome:
                    novo_barro_dict = {
                        "codigo": novo_cod.strip().upper(),
                        "nome": novo_nome.strip(),
                        "tipo_base": novo_tipo,
                        "localidade": nova_loc.strip(),
                        "status": "Ativo"
                    }
                    st.session_state.catalogo_barros = pd.concat([st.session_state.catalogo_barros, pd.DataFrame([novo_barro_dict])], ignore_index=True)
                    st.success(f"✅ Barro `{novo_cod.upper()}` cadastrado com sucesso e liberado para uso!")
                    st.rerun()
                else:
                    st.error("Preencha o Código e o Nome do Barro.")

    with col_cad2:
        st.subheader("📋 Barros Cadastrados no Sistema")
        st.dataframe(st.session_state.catalogo_barros, use_container_width=True)
        st.info("💡 **Dica:** Barros cadastrados aqui aparecem automaticamente na seleção das abas de Diagnóstico e Registro de Análise.")
