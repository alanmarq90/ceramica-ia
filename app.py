# ============================================================
# CERÂMICAIÁ v9.0 — Com Persistência Local e Edição de Chaves (Código)
# ============================================================

import io
import os  # Adicionado para suporte à persistência em disco
import urllib.parse
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="CerâmicaIA — Gestão de Barros e Misturas",
    page_icon="🧱",
    layout="wide",
)

# Estilização
st.markdown(
    """
    <style>
    .main-header {font-size: 28px; font-weight: bold; color: #b23b00;}
    .sub-header {font-size: 16px; color: #555555;}
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-header">🧱 CerâmicaIA — Otimizador de Misturas e'
    " Rastreabilidade</div>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Previsão em tempo real, controle de corte'
    " dimensional, gestão de barros e cálculo de perdas</div>",
    unsafe_allow_html=True,
)
st.divider()

# ============================================================
# PERSISTÊNCIA DE DADOS EM DISCO (EVITA RESET NO IPHONE)
# ============================================================
BARROS_INICIAIS = [
    {
        "codigo": "01_BR_ARG_PRETO_SV",
        "nome": "Barro Argiloso Preto (São Vicente)",
        "tipo_base": "Preto",
        "localidade": "São Vicente (SV)",
        "status": "Ativo",
    },
    {
        "codigo": "02_BR_ARG_VERM_STPREZ",
        "nome": "Barro Argiloso Vermelho (Sítio Prazeres)",
        "tipo_base": "Preto",
        "localidade": "Sítio Prazeres (STPRAZ)",
        "status": "Ativo",
    },
    {
        "codigo": "03_BR_AREN_BRANCO_STPRAZ",
        "nome": "Barro Arenoso Branco (Sítio Prazeres)",
        "tipo_base": "Branco",
        "localidade": "Sítio Prazeres (STPRAZ)",
        "status": "Ativo",
    },
]

HISTORICO_BASE_CSV = """data,modo,cod_barro_preto,cod_barro_amarelo,cod_barro_branco,preto_a,amarelo_a,branco_a,preto_b,amarelo_b,branco_b,pct_preto,pct_amarelo,pct_branco,umidade,residuo,retracao,esp_parede,peso,comprimento,tipo_bloco,class_residuo,excesso_peso,observacoes
2025-03-20,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,17.0,33.7,3,0.90,3.600,20.4,01-BLP,fraco,800,Histórico inicial
2025-03-21,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,17.0,32.0,3,0.85,3.185,20.5,01-BLP,limite,385,Histórico inicial
2025-03-24,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,10.0,28.0,3,0.82,3.100,20.7,01-BLP,ideal,300,Histórico inicial
2025-03-25,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,15.0,29.0,3,0.80,3.125,20.5,01-BLP,ideal,325,Histórico inicial
2025-03-27,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,16.0,31.5,3,0.85,3.184,20.5,01-BLP,ideal,384,Histórico inicial
2025-08-18,Unica,02_BR_ARG_VERM_STPREZ,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,14.0,32.0,4,0.675,3.020,20.1,01-BLP,limite,220,Histórico Clessinho / Prazeres
2026-09-02,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,1,1,3,1,2,0.550,0.183,0.267,17.0,30.0,3,0.68,2.935,20.3,01-BLP,ideal,135,Histórico recente 3 barros"""

# 1. Carregar ou Inicializar Catálogo de Barros com persistência local
if "catalogo_barros" not in st.session_state:
  if os.path.exists("db_catalogo_barros.csv"):
    st.session_state.catalogo_barros = pd.read_csv("db_catalogo_barros.csv")
  else:
    st.session_state.catalogo_barros = pd.DataFrame(BARROS_INICIAIS)
    st.session_state.catalogo_barros.to_csv(
        "db_catalogo_barros.csv", index=False
    )

# 2. Carregar ou Inicializar Base Histórica com persistência local
if "df_master" not in st.session_state:
  if os.path.exists("db_df_master.csv"):
    st.session_state.df_master = pd.read_csv("db_df_master.csv")
  else:
    st.session_state.df_master = pd.read_csv(io.StringIO(HISTORICO_BASE_CSV))
    st.session_state.df_master.to_csv("db_df_master.csv", index=False)

# 3. Carregar ou Inicializar Análises de Barro Puro com persistência local
if "analises_puro" not in st.session_state:
  if os.path.exists("db_analises_puro.csv"):
    st.session_state.analises_puro = pd.read_csv("db_analises_puro.csv")
  else:
    st.session_state.analises_puro = pd.DataFrame(columns=[
        "data",
        "codigo_barro",
        "peso_amostra_g",
        "peso_residuo_g",
        "pct_residuo_puro",
        "observacoes",
    ])
    st.session_state.analises_puro.to_csv("db_analises_puro.csv", index=False)

if "diagnostico_gerado" not in st.session_state:
  st.session_state.diagnostico_gerado = False


# Carregar Modelos Treinados
@st.cache_resource
def carregar_modelos():
  m_res = joblib.load("modelo_residuo.pkl")
  m_ret = joblib.load("modelo_retracao.pkl")
  m_pes = joblib.load("modelo_peso.pkl")
  return m_res, m_ret, m_pes


try:
  m_res, m_ret, m_pes = carregar_modelos()
except Exception as e:
  st.error(f"Erro ao carregar os arquivos de modelo .pkl: {e}")
  st.stop()

# CATALOGO DE PRODUTOS
CATALOGO_PRODUTOS = {
    "01-BLP (9x19x19 cm) — Vedação Padrão": {
        "largura": 9,
        "comprimento_nominal": 19,
        "comp_seco_ideal": 20.0,
        "peso_padrao": 2.800,
        "codigo": "01-BLP",
    },
    "BP14 (14x19x19 cm) — Estrutural Curto": {
        "largura": 14,
        "comprimento_nominal": 19,
        "comp_seco_ideal": 20.0,
        "peso_padrao": 3.800,
        "codigo": "BP14",
    },
    "02-BLG (9x19x39 cm) — Bloco Grande / Canaleta 9": {
        "largura": 9,
        "comprimento_nominal": 39,
        "comp_seco_ideal": 40.0,
        "peso_padrao": 5.500,
        "codigo": "02-BLG",
    },
    "BG14 (14x19x39 cm) — Estrutural Grande 14": {
        "largura": 14,
        "comprimento_nominal": 39,
        "comp_seco_ideal": 40.0,
        "peso_padrao": 7.000,
        "codigo": "BG14",
    },
}

# ABAS PRINCIPAIS
tab_diag, tab_reg, tab_puro, tab_barros = st.tabs([
    "🔮 Diagnóstico & Previsão",
    "📝 Registrar Análise de Mistura",
    "🧪 Análise de Barro Puro (Recebimento)",
    "🧱 Cadastrar / Gerenciar Barros",
])

# ============================================================
# ABA 1: DIAGNÓSTICO E PREVISÃO
# ============================================================
with tab_diag:
  st.sidebar.header("⚙️ Configurações do Lote")

  produto_sel = st.sidebar.selectbox(
      "Selecione o Produto em Produção:", list(CATALOGO_PRODUTOS.keys())
  )

  dados_prod = CATALOGO_PRODUTOS[produto_sel]
  largura_cm = dados_prod["largura"]
  comp_seco_ideal = dados_prod["comp_seco_ideal"]
  peso_padrao = dados_prod["peso_padrao"]
  codigo_prod = dados_prod["codigo"]

  st.sidebar.info(
      f"**Meta de Peso Padrão:** {peso_padrao:.3f} kg\n\n**Comprimento Seco"
      f" Ideal:** {comp_seco_ideal:.1f} cm (para resultar em"
      f" {dados_prod['comprimento_nominal']} cm após queima)"
  )

  st.header("🧱 Seleção dos Barros Cadastrados")
  df_barros_ativos = st.session_state.catalogo_barros[
      st.session_state.catalogo_barros["status"] == "Ativo"
  ]

  barros_pretos = df_barros_ativos[df_barros_ativos["tipo_base"] == "Preto"][
      "codigo"
  ].tolist()
  barros_amarelos = ["Nenhum"] + df_barros_ativos[
      df_barros_ativos["tipo_base"] == "Amarelo"
  ]["codigo"].tolist()
  barros_brancos = ["Nenhum"] + df_barros_ativos[
      df_barros_ativos["tipo_base"] == "Branco"
  ]["codigo"].tolist()

  col_b1, col_b2, col_b3 = st.columns(3)
  with col_b1:
    sel_barro_preto = st.selectbox(
        "Barro Argiloso (Forte):",
        barros_pretos if barros_pretos else ["01_BR_ARG_PRETO_SV"],
    )
  with col_b2:
    sel_barro_amarelo = st.selectbox(
        "Barro Intermediário (Médio):", barros_amarelos
    )
  with col_b3:
    sel_barro_branco = st.selectbox(
        "Barro Arenoso (Fraco):",
        barros_brancos
        if len(barros_brancos) > 1
        else ["03_BR_AREN_BRANCO_STPRAZ"],
    )

  st.divider()
  st.header("🏗️ Composição em Conchas")

  modo = st.radio(
      "Tipo de Produção do Dia:",
      ["Receita Única", "Mistura Mesclada (Alternada)"],
      horizontal=True,
  )

  if modo == "Receita Única":
    c1, c2, c3 = st.columns(3)
    with c1:
      preto_a = st.number_input("Conchas de Preto", 0, 10, 4, 1)
    with c2:
      amarelo_a = st.number_input(
          "Conchas de Amarelo", 0, 10, 0 if sel_barro_amarelo == "Nenhum" else 1, 1
      )
    with c3:
      branco_a = st.number_input(
          "Conchas de Branco", 0, 10, 1 if sel_barro_branco != "Nenhum" else 0, 1
      )

    preto_b, amarelo_b, branco_b = preto_a, amarelo_a, branco_a
    tot_a = max(1, preto_a + amarelo_a + branco_a)
    pct_preto = preto_a / tot_a
    pct_amarelo = amarelo_a / tot_a
    pct_branco = branco_a / tot_a
    mistura_desc = (
        f"{preto_a}x{amarelo_a}x{branco_a}"
        if amarelo_a > 0
        else f"{preto_a}x{branco_a}"
    )

  else:
    st.subheader("Receita A")
    c1, c2, c3 = st.columns(3)
    with c1:
      preto_a = st.number_input("Preto (A)", 0, 10, 4, 1)
    with c2:
      amarelo_a = st.number_input("Amarelo (A)", 0, 10, 0, 1)
    with c3:
      branco_a = st.number_input("Branco (A)", 0, 10, 1, 1)

    st.subheader("Receita B")
    c4, c5, c6 = st.columns(3)
    with c4:
      preto_b = st.number_input("Preto (B)", 0, 10, 4, 1)
    with c5:
      amarelo_b = st.number_input("Amarelo (B)", 0, 10, 0, 1)
    with c6:
      branco_b = st.number_input("Branco (B)", 0, 10, 2, 1)

    tot_a = max(1, preto_a + amarelo_a + branco_a)
    tot_b = max(1, preto_b + amarelo_b + branco_b)

    pct_preto = ((preto_a / tot_a) + (preto_b / tot_b)) / 2
    pct_amarelo = ((amarelo_a / tot_a) + (amarelo_b / tot_b)) / 2
    pct_branco = ((branco_a / tot_a) + (branco_b / tot_b)) / 2
    mistura_desc = f"Mesclada ({preto_a}x{branco_a} e {preto_b}x{branco_b})"

  st.caption(
      f"📊 **Massa Resultante na Maromba:** {pct_preto*100:.1f}% Argiloso |"
      f" {pct_amarelo*100:.1f}% Médio | {pct_branco*100:.1f}% Arenoso"
  )

  st.divider()
  st.header("🔬 Parâmetros de Processo e Dimensão de Corte")

  col_u, col_e, col_c = st.columns(3)
  with col_u:
    umidade = st.number_input("Umidade do Barro (%)", 5.0, 30.0, 16.0, 0.5)
  with col_e:
    esp_parede = st.number_input(
        "Espessura da Parede (cm)", 0.20, 1.50, 0.65, 0.01
    )
  with col_c:
    comprimento_cm = st.number_input(
        "Comprimento Seco do Bloco (cm):",
        15.0,
        45.0,
        float(comp_seco_ideal),
        0.1,
        help=(
            f"Tamanho ideal seco para este produto é {comp_seco_ideal:.1f} cm."
            " Se a guilhotina cortar maior (ex: 20,4 cm), o peso aumenta!"
        ),
    )

  st.divider()

  if st.button(
      "🔮 GERAR DIAGNÓSTICO DO LOTE", type="primary", use_container_width=True
  ):
    st.session_state.diagnostico_gerado = True

  if st.session_state.diagnostico_gerado:
    X_input = pd.DataFrame([{
        "pct_preto": pct_preto,
        "pct_amarelo": pct_amarelo,
        "pct_branco": pct_branco,
        "umidade": umidade,
        "esp_parede": esp_parede,
        "largura_cm": largura_cm,
        "comprimento_cm": comprimento_cm,
    }])

    pred_res = m_res.predict(X_input)[0]
    pred_ret = m_ret.predict(X_input)[0]
    pred_pes = m_pes.predict(X_input)[0]

    st.header("📊 Resultados Previstos pela IA")

    # ALERTA DE CORTE DIMENSIONAL
    diff_comp = comprimento_cm - comp_seco_ideal
    if diff_comp > 0.15:
      st.warning(
          f"📏 **ALERTA DE CORTE NO CARRETEL:** Bloco seco cortado com"
          f" **{comprimento_cm:.1f} cm** (+{diff_comp*10:.0f} mm acima do ideal"
          f" de {comp_seco_ideal:.1f} cm). Esse excesso de comprimento aumenta"
          " o peso do bloco! Ajuste a guilhotina da extrusora."
      )
    elif diff_comp < -0.15:
      st.warning(
          f"📏 **ATENÇÃO AO CORTE:** Bloco seco cortado com"
          f" **{comprimento_cm:.1f} cm** (-{abs(diff_comp)*10:.0f} mm abaixo do"
          f" ideal de {comp_seco_ideal:.1f} cm). Risco de ficar curto após a"
          " queima."
      )

    res1, res2, res3 = st.columns(3)

    with res1:
      st.metric("Resíduo Previsto", f"{pred_res:.1f}%")
      if pred_res > 32.0:
        class_res, msg_res = (
            "🔴 BLOCO FRACO / QUEBRADIÇO",
            "Resíduo acima de 32%. Aumente o barro Preto ou reduza o Branco.",
        )
        st.error(class_res)
      elif pred_res < 28.0:
        class_res, msg_res = (
            "🔴 FORTE DEMAIS / RISCO TRINCA",
            "Resíduo abaixo de 28%. Adicione mais barro Branco.",
        )
        st.warning(class_res)
      else:
        class_res, msg_res = (
            "🟢 FAIXA IDEAL (28% a 32%)",
            "Excelente resistência e equilíbrio plástico.",
        )
        st.success(class_res)
      st.caption(msg_res)

    with res2:
      st.metric("Retração Prevista", f"{pred_ret:.1f}%")
      comp_estimado_queimado = comprimento_cm * (1 - (pred_ret / 100))
      st.caption(
          f"Comprimento Fired/Queimado Est.: **{comp_estimado_queimado:.1f} cm**"
      )
      if pred_ret > 4.5:
        st.warning("⚡ Retração Elevada (Atenção no secador)")
      else:
        st.success("✅ Retração Sob Controle")

    excesso_g = (pred_pes - peso_padrao) * 1000
    with res3:
      st.metric(
          "Peso Previsto",
          f"{pred_pes:.3f} kg",
          delta=f"{excesso_g:+.0f}g vs Padrão",
          delta_color="inverse",
      )
      if excesso_g > 50:
        st.error("⚠️ ACIMA DO PADRÃO")
      elif excesso_g < -50:
        st.warning("⚠️ ABAIXO DO PADRÃO (Risco Estrutural)")
      else:
        st.success("✅ DENTRO DO PESO PADRÃO")

    texto_fin_wa = ""
    if excesso_g > 0:
      st.divider()
      st.subheader("💸 Impacto Financeiro (Excesso de Massa)")
      c_p1, c_p2 = st.columns(2)
      with c_p1:
        prod_dia = st.number_input(
            "Produção Planejada do Dia (blocos):", 1000, 200000, 50000, 5000
        )
      with c_p2:
        custo_barro = st.number_input(
            "Custo da Tonelada do Barro (R$/ton):", 10.0, 200.0, 50.0, 5.0
        )

      ton_perdidas_dia = (excesso_g / 1000 * prod_dia) / 1000
      prejuizo_dia = ton_perdidas_dia * custo_barro
      prejuizo_mes = prejuizo_dia * 25

      st.error(f"""
                🚨 **Alerta de Perda de Matéria-Prima:**
                - **Desperdício de Massa:** {ton_perdidas_dia:.2f} toneladas de barro/dia
                - **Prejuízo Estimado no Dia:** R$ {prejuizo_dia:,.2f}
                - **Impacto Estimado no Mês (25 dias):** R$ {prejuizo_mes:,.2f}
            """)
      texto_fin_wa = (
          f"\n💸 *PREJUÍZO EST.:* R$ {prejuizo_dia:,.0f}/dia"
          f" ({ton_perdidas_dia:.1f} ton desperdiçadas)"
      )

    st.divider()
    msg_wa_diag = f"""🧱 *CerâmicaIA — Diagnóstico de Mistura*
        
📌 *Produto:* {codigo_prod} ({largura_cm}x19x{dados_prod['comprimento_nominal']}cm)
🧱 *Barro Argiloso:* {sel_barro_preto}
🧱 *Barro Arenoso:* {sel_barro_branco}
📊 *Mistura:* {mistura_desc} | 💧 *Umid:* {umidade}% | 📏 *Esp:* {esp_parede}cm
📏 *Comp. Seco:* {comprimento_cm:.1f} cm (Ideal: {comp_seco_ideal:.1f} cm)

📊 *PREVISÃO DA IA:*
• *Resíduo:* {pred_res:.1f}% ({class_res})
• *Retração:* {pred_ret:.1f}% (Final queimado Est: {comp_estimado_queimado:.1f} cm)
• *Peso Est.:* {pred_pes:.3f} kg ({excesso_g:+.0f}g vs Meta){texto_fin_wa}

💡 *Gerado pelo CerâmicaIA App*"""

    wa_url_diag = f"https://wa.me/?text={urllib.parse.quote(msg_wa_diag)}"
    st.link_button(
        "📲 Compartilhar Diagnóstico no WhatsApp",
        wa_url_diag,
        type="secondary",
        use_container_width=True,
    )

# ============================================================
# ABA 2: REGISTRAR ANÁLISE REAL DE MISTURA
# ============================================================
with tab_reg:
  st.header("📝 Registrar Análise de Laboratório (Mistura Extrudada)")
  st.caption(
      "Alimente o sistema com os dados medidos do bloco final para calibrar o"
      " aprendizado da IA."
  )

  df_barros_ativos_reg = st.session_state.catalogo_barros[
      st.session_state.catalogo_barros["status"] == "Ativo"
  ]
  barros_pretos_reg = df_barros_ativos_reg[
      df_barros_ativos_reg["tipo_base"] == "Preto"
  ]["codigo"].tolist()
  barros_amarelos_reg = ["Nenhum"] + df_barros_ativos_reg[
      df_barros_ativos_reg["tipo_base"] == "Amarelo"
  ]["codigo"].tolist()
  barros_brancos_reg = ["Nenhum"] + df_barros_ativos_reg[
      df_barros_ativos_reg["tipo_base"] == "Branco"
  ]["codigo"].tolist()

  with st.form("form_registro_lote", clear_on_submit=True):
    st.subheader("1. Identificação e Barro Utilizado")
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
      data_lote = st.date_input("Data do Teste", datetime.now())
      prod_lote = st.selectbox(
          "Produto Testado", list(CATALOGO_PRODUTOS.keys())
      )
      codigo_selecionado = CATALOGO_PRODUTOS[prod_lote]["codigo"]
      comp_seco_sugerido = CATALOGO_PRODUTOS[prod_lote]["comp_seco_ideal"]
    with f_col2:
      cod_p_reg = st.selectbox(
          "Código Barro Preto:",
          barros_pretos_reg if barros_pretos_reg else ["01_BR_ARG_PRETO_SV"],
      )
      cod_a_reg = st.selectbox("Código Barro Amarelo:", barros_amarelos_reg)
      cod_b_reg = st.selectbox(
          "Código Barro Branco:",
          barros_brancos_reg
          if len(barros_brancos_reg) > 1
          else ["03_BR_AREN_BRANCO_STPRAZ"],
      )
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

    st.subheader("3. Medições Reais do Laboratório e Dimensão de Corte")
    f_col4, f_col5, f_col6, f_col7 = st.columns(4)
    with f_col4:
      umidade_real = st.number_input(
          "Umidade Real (%)", 0.0, 40.0, 16.0, 0.1
      )
    with f_col5:
      residuo_real = st.number_input(
          "Resíduo Real (%)", 0.0, 50.0, 30.0, 0.1
      )
    with f_col6:
      retracao_real = st.number_input(
          "Retração Real (%)", 0.0, 10.0, 3.0, 0.1
      )
    with f_col7:
      esp_real = st.number_input(
          "Espessura Parede (cm)", 0.0, 2.0, 0.65, 0.01
      )

    f_col8, f_col9, f_col10 = st.columns(3)
    with f_col8:
      comp_real_medido = st.number_input(
          "Comprimento Seco Medido (cm):",
          10.0,
          50.0,
          float(comp_seco_sugerido),
          0.1,
          help=(
              "Tamanho medido com paquímetro/trena no bloco seco (ex: 20.4 cm)"
          ),
      )
    with f_col9:
      peso_real = st.number_input(
          "Peso Real Medido (kg)", 0.0, 15.0, 3.100, 0.001
      )
    with f_col10:
      obs_texto = st.text_area("💬 Observações:", "Teste de rotina")

    btn_salvar = st.form_submit_button(
        "💾 Salvar Registro e Unificar Base",
        type="primary",
        use_container_width=True,
    )

    if btn_salvar:
      tot_a_l = max(1, p_a + a_a + b_a)
      tot_b_l = max(1, p_b + a_b + b_b)
      pct_p_l = ((p_a / tot_a_l) + (p_b / tot_b_l)) / 2
      pct_a_l = ((a_a / tot_a_l) + (a_b / tot_b_l)) / 2
      pct_b_l = ((b_a / tot_a_l) + (b_b / tot_b_l)) / 2

      class_res_l = (
          "fraco"
          if residuo_real > 32
          else ("forte" if residuo_real < 28 else "ideal")
      )
      peso_meta_l = CATALOGO_PRODUTOS[prod_lote]["peso_padrao"]
      excesso_l = (peso_real - peso_meta_l) * 1000

      novo_row = {
          "data": data_lote.strftime("%Y-%m-%d"),
          "modo": modo_lote,
          "cod_barro_preto": cod_p_reg,
          "cod_barro_amarelo": cod_a_reg,
          "cod_barro_branco": cod_b_reg,
          "preto_a": p_a,
          "amarelo_a": a_a,
          "branco_a": b_a,
          "preto_b": p_b,
          "amarelo_b": a_b,
          "branco_b": b_b,
          "pct_preto": round(pct_p_l, 3),
          "pct_amarelo": round(pct_a_l, 3),
          "pct_branco": round(pct_b_l, 3),
          "umidade": umidade_real,
          "residuo": residuo_real,
          "retracao": retracao_real,
          "esp_parede": esp_real,
          "peso": peso_real,
          "comprimento": comp_real_medido,
          "tipo_bloco": codigo_selecionado,
          "class_residuo": class_res_l,
          "excesso_peso": round(excesso_l, 0),
          "observacoes": obs_texto,
      }

      st.session_state.df_master = pd.concat(
          [pd.DataFrame([novo_row]), st.session_state.df_master],
          ignore_index=True,
      )

      # Persistir gravação de teste em disco local
      st.session_state.df_master.to_csv("db_df_master.csv", index=False)

      st.success("✅ Lote registrado com sucesso com o Comprimento Seco Medido!")

      msg_wa_reg = f"""📝 *CerâmicaIA — Registro de Lab Real*
            
📌 *Data:* {data_lote.strftime('%d/%m/%Y')} | *Produto:* {codigo_selecionado}
🧱 *Barro Preto:* {cod_p_reg} | *Branco:* {cod_b_reg}
🧪 *MENSURAÇÕES REAIS:*
• *Resíduo:* {residuo_real}% ({class_res_l.upper()})
• *Umidade:* {umidade_real}% | *Retração:* {retracao_real}%
• *Comp. Seco:* {comp_real_medido:.1f} cm | *Espessura:* {esp_real} cm
• *Peso Real:* {peso_real:.3f} kg ({excesso_l:+.0f}g vs meta)

💬 *Obs:* {obs_texto}"""

      wa_url_reg = f"https://wa.me/?text={urllib.parse.quote(msg_wa_reg)}"
      st.link_button(
          "📲 Compartilhar Teste de Lab no WhatsApp", wa_url_reg
      )

  st.divider()
  st.subheader(
      f"📋 Base de Dados Completa da Fábrica ({len(st.session_state.df_master)}"
      " Lotes Totais)"
  )
  st.dataframe(st.session_state.df_master, use_container_width=True)

  csv_completo = st.session_state.df_master.to_csv(index=False).encode("utf-8")
  st.download_button(
      label=(
          "📥 BAIXAR PLANILHA COMPLETA ATUALIZADA PARA RE-TREINO NA IA (CSV)"
      ),
      data=csv_completo,
      file_name=(
          "ceramica_lotes_completo_para_colab_"
          f"{datetime.now().strftime('%Y%m%d')}.csv"
      ),
      mime="text/csv",
      type="primary",
      use_container_width=True,
  )

# ============================================================
# ABA 3: ANÁLISE DE BARRO PURO (RECEBIMENTO DE CAMINHÃO)
# ============================================================
with tab_puro:
  st.header("🧪 Controle de Qualidade na Entrada — Barro Puro (Jazida)")
  st.caption(
      "Registre a quantidade de areia/resíduo da matéria-prima pura que chega"
      " dos caminhões."
  )

  df_barros_ativos_puro = st.session_state.catalogo_barros[
      st.session_state.catalogo_barros["status"] == "Ativo"
  ]
  lista_barros_puro = df_barros_ativos_puro["codigo"].tolist()

  col_puro1, col_puro2 = st.columns([1, 2])

  with col_puro1:
    st.subheader("➕ Novo Teste de Barro Puro")
    with st.form("form_barro_puro", clear_on_submit=True):
      data_puro = st.date_input("Data da Amostra", datetime.now())
      cod_puro_sel = st.selectbox(
          "Selecione o Barro Puro:",
          lista_barros_puro
          if lista_barros_puro
          else ["01_BR_ARG_PRETO_SV"],
      )

      peso_amostra = st.number_input(
          "Peso da Amostra Seca (g):",
          min_value=1.0,
          max_value=1000.0,
          value=100.0,
          step=10.0,
      )
      peso_residuo_puro = st.number_input(
          "Peso do Resíduo Seco Retido (g):",
          min_value=0.0,
          max_value=500.0,
          value=35.0,
          step=1.0,
      )

      pct_calculada = (
          (peso_residuo_puro / peso_amostra) * 100 if peso_amostra > 0 else 0
      )
      st.info(f"📊 **Resíduo do Barro Puro:** {pct_calculada:.1f}%")

      obs_puro = st.text_area(
          "Observações (Lote/Caminhão):", "Caminhão 01 - Jazida Nova"
      )

      btn_salvar_puro = st.form_submit_button(
          "🧪 Salvar Laudo do Barro Puro",
          type="primary",
          use_container_width=True,
      )

      if btn_salvar_puro:
        novo_puro_dict = {
            "data": data_puro.strftime("%Y-%m-%d"),
            "codigo_barro": cod_puro_sel,
            "peso_amostra_g": peso_amostra,
            "peso_residuo_g": peso_residuo_puro,
            "pct_residuo_puro": round(pct_calculada, 2),
            "observacoes": obs_puro,
        }

        st.session_state.analises_puro = pd.concat(
            [pd.DataFrame([novo_puro_dict]), st.session_state.analises_puro],
            ignore_index=True,
        )

        # Persistir teste de barro puro em disco local
        st.session_state.analises_puro.to_csv("db_analises_puro.csv", index=False)

        st.success(
            f"✅ Laudo do Barro `{cod_puro_sel}` ({pct_calculada:.1f}% resíduo)"
            " registrado com sucesso!"
        )

  with col_puro2:
    st.subheader("📋 Histórico de Qualidade dos Barros Puros (Jazida)")
    if len(st.session_state.analises_puro) > 0:
      st.dataframe(st.session_state.analises_puro, use_container_width=True)
    else:
      st.info("Nenhum teste de barro puro registrado ainda nesta sessão.")

# ============================================================
# ABA 4: CADASTRO E GESTÃO DE BARROS / JAZIDAS
# ============================================================
with tab_barros:
  st.header("🧱 Cadastro e Controle de Barros / Jazidas")
  st.caption(
      "Cadastre novas jazidas, edite informações ou inative barros esgotados."
  )

  col_cad1, col_cad2 = st.columns(2)

  with col_cad1:
    st.subheader("➕ Cadastrar Novo Barro")
    with st.form("form_novo_barro", clear_on_submit=True):
      novo_cod = st.text_input(
          "Código Oficial (ex: 04_BR_ARG_PRETO_JAZIDA2):"
      )
      novo_nome = st.text_input("Nome / Apelido Comercial:")
      novo_tipo = st.selectbox(
          "Tipo Base para IA:", ["Preto", "Amarelo", "Branco"]
      )
      nova_loc = st.text_input("Localidade / Jazida:")

      btn_cad_barro = st.form_submit_button(
          "🧱 Cadastrar Barro", type="primary", use_container_width=True
      )

      if btn_cad_barro:
        if novo_cod and novo_nome:
          cod_clean = novo_cod.strip().upper()
          if (
              cod_clean
              in st.session_state.catalogo_barros["codigo"].values
          ):
            st.error(f"❌ O código `{cod_clean}` já está cadastrado!")
          else:
            novo_barro_dict = {
                "codigo": cod_clean,
                "nome": novo_nome.strip(),
                "tipo_base": novo_tipo,
                "localidade": nova_loc.strip(),
                "status": "Ativo",
            }
            st.session_state.catalogo_barros = pd.concat(
                [
                    st.session_state.catalogo_barros,
                    pd.DataFrame([novo_barro_dict]),
                ],
                ignore_index=True,
            )

            # Persistir cadastro novo em disco local
            st.session_state.catalogo_barros.to_csv(
                "db_catalogo_barros.csv", index=False
            )

            st.success(f"✅ Barro `{cod_clean}` cadastrado!")
            st.rerun()
        else:
          st.error("Preencha o Código e o Nome do Barro.")

  with col_cad2:
    st.subheader("✏️ Editar Barro / Jazida Existente")
    lista_barros_cod = st.session_state.catalogo_barros["codigo"].tolist()

    if len(lista_barros_cod) > 0:
      barro_edit_sel = st.selectbox(
          "Selecione o Barro para Editar:", lista_barros_cod
      )
      dados_atual = st.session_state.catalogo_barros[
          st.session_state.catalogo_barros["codigo"] == barro_edit_sel
      ].iloc[0]

      with st.form("form_editar_barro"):
        # ATUALIZAÇÃO v9.0: Campo para editar o próprio código!
        edit_cod = st.text_input(
            "Código Oficial (Editar se necessário):", value=dados_atual["codigo"]
        )
        edit_nome = st.text_input("Nome / Apelido:", value=dados_atual["nome"])
        lista_tipos = ["Preto", "Amarelo", "Branco"]
        idx_tipo = (
            lista_tipos.index(dados_atual["tipo_base"])
            if dados_atual["tipo_base"] in lista_tipos
            else 0
        )
        edit_tipo = st.selectbox(
            "Tipo Base para IA:", lista_tipos, index=idx_tipo
        )
        edit_loc = st.text_input(
            "Localidade / Jazida:", value=dados_atual["localidade"]
        )
        lista_status = ["Ativo", "Inativo"]
        idx_status = (
            lista_status.index(dados_atual["status"])
            if dados_atual["status"] in lista_status
            else 0
        )
        edit_status = st.selectbox(
            "Status no Sistema:", lista_status, index=idx_status
        )

        btn_salvar_edit = st.form_submit_button(
            "💾 Salvar Alterações", type="primary", use_container_width=True
        )

        if btn_salvar_edit:
          idx_muda = st.session_state.catalogo_barros[
              st.session_state.catalogo_barros["codigo"] == barro_edit_sel
          ].index[0]

          edit_cod_clean = edit_cod.strip().upper()

          if not edit_cod_clean:
            st.error("❌ O código do barro não pode ser vazio.")
          # Valida se o novo código já existe em outro registro que não seja ele mesmo
          elif (
              edit_cod_clean != barro_edit_sel
              and edit_cod_clean
              in st.session_state.catalogo_barros["codigo"].values
          ):
            st.error(
                f"❌ O código `{edit_cod_clean}` já existe em outro cadastro!"
            )
          else:
            # 1. ATUALIZAÇÃO EM CASCATA: Se mudou o código chave, varre os históricos e atualiza as referências
            if edit_cod_clean != barro_edit_sel:
              # Na tabela df_master (Histórico de Produção)
              st.session_state.df_master["cod_barro_preto"] = (
                  st.session_state.df_master["cod_barro_preto"].replace(
                      barro_edit_sel, edit_cod_clean
                  )
              )
              st.session_state.df_master["cod_barro_amarelo"] = (
                  st.session_state.df_master["cod_barro_amarelo"].replace(
                      barro_edit_sel, edit_cod_clean
                  )
              )
              st.session_state.df_master["cod_barro_branco"] = (
                  st.session_state.df_master["cod_barro_branco"].replace(
                      barro_edit_sel, edit_cod_clean
                  )
              )
              # Salva base histórica atualizada
              st.session_state.df_master.to_csv("db_df_master.csv", index=False)

              # Na tabela analises_puro (Laboratório do Barro Puro)
              st.session_state.analises_puro["codigo_barro"] = (
                  st.session_state.analises_puro["codigo_barro"].replace(
                      barro_edit_sel, edit_cod_clean
                  )
              )
              # Salva base de barro puro atualizada
              st.session_state.analises_puro.to_csv(
                  "db_analises_puro.csv", index=False
              )

            # 2. Atualiza o cadastro do Barro
            st.session_state.catalogo_barros.at[idx_muda, "codigo"] = (
                edit_cod_clean
            )
            st.session_state.catalogo_barros.at[idx_muda, "nome"] = (
                edit_nome.strip()
            )
            st.session_state.catalogo_barros.at[idx_muda, "tipo_base"] = (
                edit_tipo
            )
            st.session_state.catalogo_barros.at[idx_muda, "localidade"] = (
                edit_loc.strip()
            )
            st.session_state.catalogo_barros.at[idx_muda, "status"] = (
                edit_status
            )

            # 3. Salva em disco local de forma persistente
            st.session_state.catalogo_barros.to_csv(
                "db_catalogo_barros.csv", index=False
            )

            st.success(
                "✅ Barro atualizado e referências corrigidas em cascata!"
            )
            st.rerun()

  st.divider()
  st.subheader("📋 Tabela Geral de Barros Cadastrados")
  st.dataframe(st.session_state.catalogo_barros, use_container_width=True)
