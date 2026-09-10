# ============================================================
# CERÂMICAIÁ v2.0 — Dashboard com Registro e Memória de Estado
# ============================================================

import streamlit as st
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="CerâmicaIA — Inteligência de Mistura",
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

st.markdown('<div class="main-header">🧱 CerâmicaIA — Otimizador de Misturas e Qualidade</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Previsão em tempo real, registro de análises e cálculo financeiro de perdas</div>', unsafe_allow_html=True)
st.divider()

# Inicializar Estados de Memória (st.session_state)
if 'diagnostico_gerado' not in st.session_state:
    st.session_state.diagnostico_gerado = False
if 'historico_lotes' not in st.session_state:
    st.session_state.historico_lotes = []

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
    st.error(f"Erro ao carregar os modelos da IA (.pkl): {e}")
    st.stop()

# CATALOGO DE PRODUTOS
CATALOGO_PRODUTOS = {
    "01-BLP (9x19x19 cm) — Vedação Padrão": {"largura": 9, "comprimento": 19, "peso_padrao": 2.800},
    "BP14 (14x19x19 cm) — Estrutural Curto": {"largura": 14, "comprimento": 19, "peso_padrao": 3.800},
    "02-BLG (9x19x39 cm) — Bloco Grande / Canaleta 9": {"largura": 9, "comprimento": 39, "peso_padrao": 5.500},
    "BG14 (14x19x39 cm) — Estrutural Grande 14": {"largura": 14, "comprimento": 39, "peso_padrao": 7.000},
}

# CRIAÇÃO DAS ABAS PRINCIPAIS
tab_diag, tab_reg = st.tabs(["🔮 Diagnóstico & Previsão", "📝 Registrar Análise Real (Alimentar IA)"])

# ============================================================
# ABA 1: DIAGNÓSTICO E PREVISÃO
# ============================================================
with tab_diag:
    st.sidebar.header("⚙️ Configurações do Produto")
    produto_sel = st.sidebar.selectbox(
        "Selecione o Produto em Produção:",
        list(CATALOGO_PRODUTOS.keys())
    )

    dados_prod = CATALOGO_PRODUTOS[produto_sel]
    largura_cm = dados_prod["largura"]
    comprimento_cm = dados_prod["comprimento"]
    peso_padrao = dados_prod["peso_padrao"]

    st.sidebar.info(f"**Meta de Peso Padrão:** {peso_padrao:.3f} kg\n\n**Dimensão:** {largura_cm}x19x{comprimento_cm} cm")

    st.header("🏗️ Composição da Mistura")
    modo = st.radio("Tipo de Produção do Dia:", ["Receita Única", "Mistura Mesclada (Alternada)"], horizontal=True)

    if modo == "Receita Única":
        c1, c2, c3 = st.columns(3)
        with c1: preto_a = st.number_input("Conchas de PRETO (BSV)", 0, 10, 4, 1)
        with c2: amarelo_a = st.number_input("Conchas de AMARELO", 0, 10, 0, 1)
        with c3: branco_a = st.number_input("Conchas de BRANCO", 0, 10, 1, 1)
        
        tot_a = max(1, preto_a + amarelo_a + branco_a)
        pct_preto = preto_a / tot_a
        pct_amarelo = amarelo_a / tot_a
        pct_branco = branco_a / tot_a

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

    st.caption(f"📊 **Massa Resultante na Maromba:** {pct_preto*100:.1f}% Preto | {pct_amarelo*100:.1f}% Amarelo | {pct_branco*100:.1f}% Branco")

    st.divider()
    st.header("🔬 Parâmetros do Processo")
    col_u, col_e = st.columns(2)
    with col_u:
        umidade = st.number_input("Umidade do Barro (%)", 5.0, 30.0, 16.0, 0.5)
    with col_e:
        esp_parede = st.number_input("Espessura da Parede (cm)", 0.20, 1.50, 0.65, 0.01)

    st.divider()
    
    # Botão ativa o Estado da Memória
    if st.button("🔮 GERAR DIAGNÓSTICO DO LOTE", type="primary", use_container_width=True):
        st.session_state.diagnostico_gerado = True

    # EXIBIÇÃO DOS RESULTADOS (Mantém visível mesmo se interagir na página!)
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
                st.error("🔴 BLOCO FRACO / QUEBRADIÇO")
                st.caption("Resíduo acima de 32%. Aumente o barro Preto ou reduza o Branco.")
            elif pred_res < 28.0:
                st.warning("🔴 FORTE DEMAIS / RISCO TRINCA")
                st.caption("Resíduo abaixo de 28%. Adicione mais barro Branco.")
            else:
                st.success("🟢 FAIXA IDEAL (28% a 32%)")
                st.caption("Excelente resistência e equilíbrio plástico.")
                
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

# ============================================================
# ABA 2: REGISTRAR ANÁLISE REAL (ALIMENTAR A IA)
# ============================================================
with tab_reg:
    st.header("📝 Registrar Análise de Laboratório Real")
    st.caption("Alimente o sistema com os dados reais medidos para enriquecer o histórico da fábrica.")
    
    with st.form("form_registro_lote", clear_on_submit=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            data_lote = st.date_input("Data do Teste", datetime.now())
            prod_lote = st.selectbox("Produto Testado", list(CATALOGO_PRODUTOS.keys()))
        with f_col2:
            modo_lote = st.selectbox("Tipo de Produção", ["Unica", "Mesclada"])
            mistura_str = st.text_input("Descrição da Receita (ex: 4x1 ou 4x1/4x2)", "4x1")
        with f_col3:
            umidade_real = st.number_input("Umidade Real (%)", 0.0, 40.0, 16.0, 0.1)
            residuo_real = st.number_input("Resíduo Real (%)", 0.0, 50.0, 30.0, 0.1)

        f_col4, f_col5, f_col6 = st.columns(3)
        with f_col4:
            retracao_real = st.number_input("Retração Real (%)", 0.0, 10.0, 3.0, 0.1)
        with f_col5:
            esp_real = st.number_input("Espessura da Parede (cm)", 0.0, 2.0, 0.65, 0.01)
        with f_col6:
            peso_real = st.number_input("Peso Real Medido (kg)", 0.0, 15.0, 3.100, 0.001)

        obs_texto = st.text_area("💬 Observações do Chão de Fábrica (ex: 'barro mais arenoso', 'pressão da maromba alta', 'curtiu 2 dias'):")
        
        btn_salvar = st.form_submit_button("💾 Salvar Registro de Lote", type="primary")
        
        if btn_salvar:
            novo_registro = {
                "Data": data_lote.strftime("%Y-%m-%d"),
                "Produto": prod_lote,
                "Tipo": modo_lote,
                "Mistura": mistura_str,
                "Umidade%": umidade_real,
                "Resíduo%": residuo_real,
                "Retração%": retracao_real,
                "Espessura_cm": esp_real,
                "Peso_kg": peso_real,
                "Observações": obs_texto
            }
            st.session_state.historico_lotes.append(novo_registro)
            st.success("✅ Lote registrado com sucesso no histórico da fábrica!")

    # Exibir Tabela de Lotes Registrados na Sessão
    if len(st.session_state.historico_lotes) > 0:
        st.divider()
        st.subheader("📋 Lotes Registrados Nesta Sessão")
        df_historico = pd.DataFrame(st.session_state.historico_lotes)
        st.dataframe(df_historico, use_container_width=True)
        
        # Botão para baixar em CSV
        csv_export = df_historico.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Planilha de Registros (CSV)",
            data=csv_export,
            file_name=f"registros_laboratorio_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
