# ============================================================
# CERAMICAIA v11.0 — SaaS com Google Sheets, Logo e UI Limpa
# ============================================================

import io
import os
import urllib.parse
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
import streamlit as st

# Importação de bibliotecas do Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================
st.set_page_config(
    page_title="CeramicaIA — Gestao de Barros e Misturas",
    page_icon="logo.png" if os.path.exists("logo.png") else None,
    layout="wide",
)

# ============================================================
# ESTILIZACAO CSS (SEM EMOJIS, VISUAL CORPORATIVO)
# ============================================================
st.markdown(
    """
    <style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #b23b00;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 14px;
        color: #666666;
        margin-top: 2px;
    }
    .status-ok {
        background-color: #d4edda;
        color: #155724;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 13px;
    }
    .status-local {
        background-color: #fff3cd;
        color: #856404;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 13px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# LOGO E CABECALHO
# ============================================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
    st.sidebar.markdown("---")

st.markdown(
    '<div class="main-header">CeramicaIA — Otimizador de Misturas e Rastreabilidade</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Previsao em tempo real, controle de corte dimensional, gestao de barros/produtos e calculo de perdas</div>',
    unsafe_allow_html=True,
)
st.divider()

# ============================================================
# CONEXAO COM GOOGLE SHEETS
# ============================================================
MODO_SHEETS = False
worksheet_lotes = None
worksheet_barros = None
worksheet_produtos = None
worksheet_puro = None

if GSPREAD_AVAILABLE:
    try:
        gcp_creds_dict = dict(st.secrets["gcp_service_account"])
        gsheet_id = st.secrets["GSHEET_ID"]

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(gcp_creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(gsheet_id)

        worksheet_lotes = spreadsheet.worksheet("lotes")
        worksheet_barros = spreadsheet.worksheet("barros")
        worksheet_produtos = spreadsheet.worksheet("produtos")
        worksheet_puro = spreadsheet.worksheet("analises_puro")

        MODO_SHEETS = True
    except Exception as e:
        st.sidebar.markdown(
            f'<div class="status-local">Banco de dados: CSV Local<br>Aviso: {str(e)[:60]}</div>',
            unsafe_allow_html=True,
        )
else:
    st.sidebar.markdown(
        '<div class="status-local">Banco de dados: CSV Local<br>Motivo: gspread nao instalado</div>',
        unsafe_allow_html=True,
    )

if MODO_SHEETS:
    st.sidebar.markdown(
        '<div class="status-ok">Banco de dados: Google Sheets Conectado</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# FUNCOES DE SINCRONIZACAO COM SHEETS
# ============================================================
def ler_dados_sheets(worksheet, colunas):
    try:
        dados = worksheet.get_all_records()
        if dados:
            return pd.DataFrame(dados)
    except Exception:
        pass
    return pd.DataFrame(columns=colunas)

def salvar_no_sheets(worksheet, df):
    try:
        worksheet.clear()
        df_str = df.astype(str)
        dados_lista = [df_str.columns.tolist()] + df_str.values.tolist()
        worksheet.update(dados_lista)
    except Exception as e:
        st.error(f"Erro ao sincronizar com Google Sheets: {e}")

# ============================================================
# DADOS INICIAIS (SEED)
# ============================================================
BARROS_INICIAIS = [
    {
        "codigo": "01_BR_ARG_PRETO_SV",
        "nome": "Barro Argiloso Preto (Sao Vicente)",
        "tipo_base": "Preto",
        "localidade": "Sao Vicente (SV)",
        "status": "Ativo",
    },
    {
        "codigo": "02_BR_ARG_VERM_STPREZ",
        "nome": "Barro Argiloso Vermelho (Sitio Prazeres)",
        "tipo_base": "Preto",
        "localidade": "Sitio Prazeres (STPRAZ)",
        "status": "Ativo",
    },
    {
        "codigo": "03_BR_AREN_BRANCO_STPRAZ",
        "nome": "Barro Arenoso Branco (Sitio Prazeres)",
        "tipo_base": "Branco",
        "localidade": "Sitio Prazeres (STPRAZ)",
        "status": "Ativo",
    },
]

PRODUTOS_INICIAIS = [
    {
        "chave_comercial": "01-BLP (9x19x19 cm) — Vedacao Padrao",
        "codigo": "01-BLP",
        "largura": 9.0,
        "comprimento_nominal": 19.0,
        "comp_seco_ideal": 20.0,
        "peso_padrao": 2.800,
        "status": "Ativo",
    },
    {
        "chave_comercial": "BP14 (14x19x19 cm) — Estrutural Curto",
        "codigo": "BP14",
        "largura": 14.0,
        "comprimento_nominal": 19.0,
        "comp_seco_ideal": 20.0,
        "peso_padrao": 3.800,
        "status": "Ativo",
    },
    {
        "chave_comercial": "02-BLG (9x19x39 cm) — Bloco Grande / Canaleta 9",
        "codigo": "02-BLG",
        "largura": 9.0,
        "comprimento_nominal": 39.0,
        "comp_seco_ideal": 40.0,
        "peso_padrao": 5.500,
        "status": "Ativo",
    },
    {
        "chave_comercial": "BG14 (14x19x39 cm) — Estrutural Grande 14",
        "codigo": "BG14",
        "largura": 14.0,
        "comprimento_nominal": 39.0,
        "comp_seco_ideal": 40.0,
        "peso_padrao": 7.000,
        "status": "Ativo",
    },
]

HISTORICO_BASE_CSV = """data,modo,cod_barro_preto,cod_barro_amarelo,cod_barro_branco,preto_a,amarelo_a,branco_a,preto_b,amarelo_b,branco_b,pct_preto,pct_amarelo,pct_branco,umidade,residuo,retracao,esp_parede,peso,comprimento,tipo_bloco,class_residuo,excesso_peso,observacoes
2025-03-20,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,17.0,33.7,3,0.90,3.600,20.4,01-BLP,fraco,800,Historico inicial
2025-03-21,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,17.0,32.0,3,0.85,3.185,20.5,01-BLP,limite,385,Historico inicial
2025-03-24,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,10.0,28.0,3,0.82,3.100,20.7,01-BLP,ideal,300,Historico inicial
2025-03-25,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,15.0,29.0,3,0.80,3.125,20.5,01-BLP,ideal,325,Historico inicial
2025-03-27,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,16.0,31.5,3,0.85,3.184,20.5,01-BLP,ideal,384,Historico inicial
2025-08-18,Unica,02_BR_ARG_VERM_STPREZ,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,14.0,32.0,4,0.675,3.020,20.1,01-BLP,limite,220,Historico Clessinho / Prazeres
2026-09-02,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,1,1,3,1,2,0.550,0.183,0.267,17.0,30.0,3,0.68,2.935,20.3,01-BLP,ideal,135,Historico recente 3 barros"""

COLUNAS_BARROS = ["codigo", "nome", "tipo_base", "localidade", "status"]
COLUNAS_PRODUTOS = ["chave_comercial", "codigo", "largura", "comprimento_nominal", "comp_seco_ideal", "peso_padrao", "status"]
COLUNAS_LOTES = [
    "data", "modo", "cod_barro_preto", "cod_barro_amarelo", "cod_barro_branco",
    "preto_a", "amarelo_a", "branco_a", "preto_b", "amarelo_b", "branco_b",
    "pct_preto", "pct_amarelo", "pct_branco", "umidade", "residuo", "retracao",
    "esp_parede", "peso", "comprimento", "tipo_bloco", "class_residuo", "excesso_peso", "observacoes"
]
COLUNAS_PURO = ["data", "codigo_barro", "peso_amostra_g", "peso_residuo_g", "pct_residuo_puro", "observacoes"]

# ============================================================
# INICIALIZACAO DOS DATAFRAMES
# ============================================================

# 1. Barros
if "catalogo_barros" not in st.session_state:
    if MODO_SHEETS and worksheet_barros:
        df_b = ler_dados_sheets(worksheet_barros, COLUNAS_BARROS)
        if len(df_b) == 0:
            df_b = pd.DataFrame(BARROS_INICIAIS)
            salvar_no_sheets(worksheet_barros, df_b)
        st.session_state.catalogo_barros = df_b
    elif os.path.exists("db_catalogo_barros.csv"):
        st.session_state.catalogo_barros = pd.read_csv("db_catalogo_barros.csv")
    else:
        st.session_state.catalogo_barros = pd.DataFrame(BARROS_INICIAIS)
        st.session_state.catalogo_barros.to_csv("db_catalogo_barros.csv", index=False)

# 2. Produtos
if "catalogo_produtos" not in st.session_state:
    if MODO_SHEETS and worksheet_produtos:
        df_p = ler_dados_sheets(worksheet_produtos, COLUNAS_PRODUTOS)
        if len(df_p) == 0:
            df_p = pd.DataFrame(PRODUTOS_INICIAIS)
            salvar_no_sheets(worksheet_produtos, df_p)
        st.session_state.catalogo_produtos = df_p
    elif os.path.exists("db_catalogo_produtos.csv"):
        st.session_state.catalogo_produtos = pd.read_csv("db_catalogo_produtos.csv")
    else:
        st.session_state.catalogo_produtos = pd.DataFrame(PRODUTOS_INICIAIS)
        st.session_state.catalogo_produtos.to_csv("db_catalogo_produtos.csv", index=False)

# 3. Lotes
if "df_master" not in st.session_state:
    if MODO_SHEETS and worksheet_lotes:
        df_l = ler_dados_sheets(worksheet_lotes, COLUNAS_LOTES)
        if len(df_l) == 0:
            df_l = pd.read_csv(io.StringIO(HISTORICO_BASE_CSV))
            salvar_no_sheets(worksheet_lotes, df_l)
        st.session_state.df_master = df_l
    elif os.path.exists("db_df_master.csv"):
        st.session_state.df_master = pd.read_csv("db_df_master.csv")
    else:
        st.session_state.df_master = pd.read_csv(io.StringIO(HISTORICO_BASE_CSV))
        st.session_state.df_master.to_csv("db_df_master.csv", index=False)

# 4. Barro Puro
if "analises_puro" not in st.session_state:
    if MODO_SHEETS and worksheet_puro:
        df_pu = ler_dados_sheets(worksheet_puro, COLUNAS_PURO)
        st.session_state.analises_puro = df_pu
    elif os.path.exists("db_analises_puro.csv"):
        st.session_state.analises_puro = pd.read_csv("db_analises_puro.csv")
    else:
        st.session_state.analises_puro = pd.DataFrame(columns=COLUNAS_PURO)
        st.session_state.analises_puro.to_csv("db_analises_puro.csv", index=False)

if "diagnostico_gerado" not in st.session_state:
    st.session_state.diagnostico_gerado = False

# ============================================================
# PERSISTENCIA CENTRALIZADA
# ============================================================
def persistir_dados(tipo):
    if tipo == "barros":
        df = st.session_state.catalogo_barros
        if MODO_SHEETS and worksheet_barros:
            salvar_no_sheets(worksheet_barros, df)
        df.to_csv("db_catalogo_barros.csv", index=False)
    elif tipo == "produtos":
        df = st.session_state.catalogo_produtos
        if MODO_SHEETS and worksheet_produtos:
            salvar_no_sheets(worksheet_produtos, df)
        df.to_csv("db_catalogo_produtos.csv", index=False)
    elif tipo == "lotes":
        df = st.session_state.df_master
        if MODO_SHEETS and worksheet_lotes:
            salvar_no_sheets(worksheet_lotes, df)
        df.to_csv("db_df_master.csv", index=False)
    elif tipo == "puro":
        df = st.session_state.analises_puro
        if MODO_SHEETS and worksheet_puro:
            salvar_no_sheets(worksheet_puro, df)
        df.to_csv("db_analises_puro.csv", index=False)

# ============================================================
# MODELOS DE IA
# ============================================================
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

# ============================================================
# ABAS DA PLATAFORMA
# ============================================================
tab_diag, tab_reg, tab_puro, tab_barros, tab_produtos = st.tabs([
    "Diagnostico e Previsao",
    "Registrar Analise de Mistura",
    "Analise de Barro Puro (Recebimento)",
    "Cadastrar / Gerenciar Barros",
    "Cadastrar / Gerenciar Produtos",
])

# ============================================================
# ABA 1: DIAGNOSTICO E PREVISAO
# ============================================================
with tab_diag:
    st.sidebar.header("Configuracoes do Lote")

    df_prod_ativos = st.session_state.catalogo_produtos[
        st.session_state.catalogo_produtos["status"] == "Ativo"
    ]

    if len(df_prod_ativos) == 0:
        st.sidebar.error("Nenhum produto ativo cadastrado! Va na aba Gerenciar Produtos.")
        st.stop()

    produto_sel = st.sidebar.selectbox(
        "Selecione o Produto em Producao:",
        df_prod_ativos["chave_comercial"].tolist(),
    )

    dados_prod = df_prod_ativos[
        df_prod_ativos["chave_comercial"] == produto_sel
    ].iloc[0]
    largura_cm = float(dados_prod["largura"])
    comp_seco_ideal = float(dados_prod["comp_seco_ideal"])
    peso_padrao = float(dados_prod["peso_padrao"])
    codigo_prod = dados_prod["codigo"]
    comprimento_nominal = float(dados_prod["comprimento_nominal"])

    st.sidebar.info(
        f"**Meta de Peso Padrao:** {peso_padrao:.3f} kg\n\n"
        f"**Comprimento Seco Ideal:** {comp_seco_ideal:.1f} cm "
        f"(para resultar em {comprimento_nominal:.1f} cm apos queima)"
    )

    st.header("Selecao dos Barros Cadastrados")
    df_barros_ativos = st.session_state.catalogo_barros[
        st.session_state.catalogo_barros["status"] == "Ativo"
    ]

    barros_pretos = df_barros_ativos[df_barros_ativos["tipo_base"] == "Preto"]["codigo"].tolist()
    barros_amarelos = ["Nenhum"] + df_barros_ativos[df_barros_ativos["tipo_base"] == "Amarelo"]["codigo"].tolist()
    barros_brancos = ["Nenhum"] + df_barros_ativos[df_barros_ativos["tipo_base"] == "Branco"]["codigo"].tolist()

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        sel_barro_preto = st.selectbox(
            "Barro Argiloso (Forte):",
            barros_pretos if barros_pretos else ["01_BR_ARG_PRETO_SV"],
        )
    with col_b2:
        sel_barro_amarelo = st.selectbox(
            "Barro Intermediario (Medio):", barros_amarelos
        )
    with col_b3:
        sel_barro_branco = st.selectbox(
            "Barro Arenoso (Fraco):",
            barros_brancos if len(barros_brancos) > 1 else ["03_BR_AREN_BRANCO_STPRAZ"],
        )

    st.divider()
    st.header("Composicao em Conchas")

    modo = st.radio(
        "Tipo de Producao do Dia:",
        ["Receita Unica", "Mistura Mesclada (Alternada)"],
        horizontal=True,
    )

    if modo == "Receita Unica":
        c1, c2, c3 = st.columns(3)
        with c1:
            preto_a = st.number_input("Conchas de Preto", 0, 10, 4, 1)
        with c2:
            amarelo_a = st.number_input("Conchas de Amarelo", 0, 10, 0 if sel_barro_amarelo == "Nenhum" else 1, 1)
        with c3:
            branco_a = st.number_input("Conchas de Branco", 0, 10, 1 if sel_barro_branco != "Nenhum" else 0, 1)

        preto_b, amarelo_b, branco_b = preto_a, amarelo_a, branco_a
        tot_a = max(1, preto_a + amarelo_a + branco_a)
        pct_preto = preto_a / tot_a
        pct_amarelo = amarelo_a / tot_a
        pct_branco = branco_a / tot_a
        mistura_desc = f"{preto_a}x{amarelo_a}x{branco_a}" if amarelo_a > 0 else f"{preto_a}x{branco_a}"

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
        f"**Massa Resultante na Maromba:** {pct_preto*100:.1f}% Argiloso | "
        f"{pct_amarelo*100:.1f}% Medio | {pct_branco*100:.1f}% Arenoso"
    )

    st.divider()
    st.header("Parametros de Processo e Dimensao de Corte")

    col_u, col_e, col_c = st.columns(3)
    with col_u:
        umidade = st.number_input("Umidade do Barro (%)", 5.0, 30.0, 16.0, 0.5)
    with col_e:
        esp_parede = st.number_input("Espessura da Parede (cm)", 0.20, 1.50, 0.65, 0.01)
    with col_c:
        comprimento_cm = st.number_input(
            "Comprimento Seco do Bloco (cm):",
            15.0, 45.0, float(comp_seco_ideal), 0.1,
            help=(
                f"Tamanho ideal seco para este produto e {comp_seco_ideal:.1f} cm. "
                "Se a guilhotina cortar maior (ex: 20,4 cm), o peso aumenta!"
            ),
        )

    st.divider()

    if st.button("GERAR DIAGNOSTICO DO LOTE", type="primary", use_container_width=True):
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

        st.header("Resultados Previstos pela IA")

        diff_comp = comprimento_cm - comp_seco_ideal
        if diff_comp > 0.15:
            st.warning(
                f"**ALERTA DE CORTE NO CARRETEL:** Bloco seco cortado com "
                f"**{comprimento_cm:.1f} cm** (+{diff_comp*10:.0f} mm acima do ideal de {comp_seco_ideal:.1f} cm). "
                "Esse excesso de comprimento aumenta o peso do bloco! Ajuste a guilhotina."
            )
        elif diff_comp < -0.15:
            st.warning(
                f"**ATENCAO AO CORTE:** Bloco seco cortado com "
                f"**{comprimento_cm:.1f} cm** (-{abs(diff_comp)*10:.0f} mm abaixo do ideal de {comp_seco_ideal:.1f} cm). "
                "Risco de ficar curto apos a queima."
            )

        res1, res2, res3 = st.columns(3)

        with res1:
            st.metric("Residuo Previsto", f"{pred_res:.1f}%")
            if pred_res > 32.0:
                class_res = "BLOCO FRACO / QUEBRADICO"
                msg_res = "Residuo acima de 32%. Aumente o barro Preto ou reduza o Branco."
                st.error(class_res)
            elif pred_res < 28.0:
                class_res = "FORTE DEMAIS / RISCO TRINCA"
                msg_res = "Residuo abaixo de 28%. Adicione mais barro Branco."
                st.warning(class_res)
            else:
                class_res = "FAIXA IDEAL (28% a 32%)"
                msg_res = "Excelente resistencia e equilibrio plastico."
                st.success(class_res)
            st.caption(msg_res)

        with res2:
            st.metric("Retracao Prevista", f"{pred_ret:.1f}%")
            comp_estimado_queimado = comprimento_cm * (1 - (pred_ret / 100))
            st.caption(f"Comprimento Queimado Est.: **{comp_estimado_queimado:.1f} cm**")
            if pred_ret > 4.5:
                st.warning("Retracao Elevada (Atencao no secador)")
            else:
                st.success("Retracao Sob Controle")

        excesso_g = (pred_pes - peso_padrao) * 1000
        with res3:
            st.metric(
                "Peso Previsto",
                f"{pred_pes:.3f} kg",
                delta=f"{excesso_g:+.0f}g vs Padrao",
                delta_color="inverse",
            )
            if excesso_g > 50:
                st.error("ACIMA DO PADRAO")
            elif excesso_g < -50:
                st.warning("ABAIXO DO PADRAO (Risco Estrutural)")
            else:
                st.success("DENTRO DO PESO PADRAO")

        texto_fin_wa = ""
        if excesso_g > 0:
            st.divider()
            st.subheader("Impacto Financeiro (Excesso de Massa)")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                prod_dia = st.number_input("Producao Planejada do Dia (blocos):", 1000, 200000, 50000, 5000)
            with c_p2:
                custo_barro = st.number_input("Custo da Tonelada do Barro (R$/ton):", 10.0, 200.0, 50.0, 5.0)

            ton_perdidas_dia = (excesso_g / 1000 * prod_dia) / 1000
            prejuizo_dia = ton_perdidas_dia * custo_barro
            prejuizo_mes = prejuizo_dia * 25

            st.error(
                f"**Alerta de Perda de Materia-Prima:**\n\n"
                f"- Desperdicio de Massa: {ton_perdidas_dia:.2f} toneladas/dia\n"
                f"- Prejuizo Estimado no Dia: R$ {prejuizo_dia:,.2f}\n"
                f"- Impacto Estimado no Mes (25 dias): R$ {prejuizo_mes:,.2f}"
            )
            texto_fin_wa = f"\nPREJUIZO EST.: R$ {prejuizo_dia:,.0f}/dia ({ton_perdidas_dia:.1f} ton desperdicadas)"

        st.divider()
        msg_wa_diag = (
            f"CeramicaIA — Diagnostico de Mistura\n\n"
            f"Produto: {codigo_prod} ({largura_cm}x19x{comprimento_nominal}cm)\n"
            f"Barro Argiloso: {sel_barro_preto}\n"
            f"Barro Arenoso: {sel_barro_branco}\n"
            f"Mistura: {mistura_desc} | Umid: {umidade}% | Esp: {esp_parede}cm\n"
            f"Comp. Seco: {comprimento_cm:.1f} cm (Ideal: {comp_seco_ideal:.1f} cm)\n\n"
            f"PREVISAO DA IA:\n"
            f"- Residuo: {pred_res:.1f}% ({class_res})\n"
            f"- Retracao: {pred_ret:.1f}% (Final queimado Est: {comp_estimado_queimado:.1f} cm)\n"
            f"- Peso Est.: {pred_pes:.3f} kg ({excesso_g:+.0f}g vs Meta){texto_fin_wa}\n\n"
            f"Gerado pelo CeramicaIA App"
        )

        wa_url_diag = f"https://wa.me/?text={urllib.parse.quote(msg_wa_diag)}"
        st.link_button("Compartilhar Diagnostico no WhatsApp", wa_url_diag, type="secondary", use_container_width=True)

# ============================================================
# ABA 2: REGISTRAR ANALISE REAL DE MISTURA
# ============================================================
with tab_reg:
    st.header("Registrar Analise de Laboratorio (Mistura Extrudada)")
    st.caption("Alimente o sistema com os dados medidos do bloco final para calibrar o aprendizado da IA.")

    df_barros_ativos_reg = st.session_state.catalogo_barros[st.session_state.catalogo_barros["status"] == "Ativo"]
    barros_pretos_reg = df_barros_ativos_reg[df_barros_ativos_reg["tipo_base"] == "Preto"]["codigo"].tolist()
    barros_amarelos_reg = ["Nenhum"] + df_barros_ativos_reg[df_barros_ativos_reg["tipo_base"] == "Amarelo"]["codigo"].tolist()
    barros_brancos_reg = ["Nenhum"] + df_barros_ativos_reg[df_barros_ativos_reg["tipo_base"] == "Branco"]["codigo"].tolist()

    df_prod_ativos_reg = st.session_state.catalogo_produtos[st.session_state.catalogo_produtos["status"] == "Ativo"]

    with st.form("form_registro_lote", clear_on_submit=True):
        st.subheader("1. Identificacao e Barro Utilizado")
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            data_lote = st.date_input("Data do Teste", datetime.now())
            prod_lote = st.selectbox("Produto Testado", df_prod_ativos_reg["chave_comercial"].tolist())
            row_prod_reg = df_prod_ativos_reg[df_prod_ativos_reg["chave_comercial"] == prod_lote].iloc[0]
            codigo_selecionado = row_prod_reg["codigo"]
            comp_seco_sugerido = float(row_prod_reg["comp_seco_ideal"])
            peso_meta_l = float(row_prod_reg["peso_padrao"])

        with f_col2:
            cod_p_reg = st.selectbox("Codigo Barro Preto:", barros_pretos_reg if barros_pretos_reg else ["01_BR_ARG_PRETO_SV"])
            cod_a_reg = st.selectbox("Codigo Barro Amarelo:", barros_amarelos_reg)
            cod_b_reg = st.selectbox("Codigo Barro Branco:", barros_brancos_reg if len(barros_brancos_reg) > 1 else ["03_BR_AREN_BRANCO_STPRAZ"])
        with f_col3:
            modo_lote = st.selectbox("Tipo de Producao", ["Unica", "Mesclada"])

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

        st.subheader("3. Medicoes Reais do Laboratorio e Dimensao de Corte")
        f_col4, f_col5, f_col6, f_col7 = st.columns(4)
        with f_col4:
            umidade_real = st.number_input("Umidade Real (%)", 0.0, 40.0, 16.0, 0.1)
        with f_col5:
            residuo_real = st.number_input("Residuo Real (%)", 0.0, 50.0, 30.0, 0.1)
        with f_col6:
            retracao_real = st.number_input("Retracao Real (%)", 0.0, 10.0, 3.0, 0.1)
        with f_col7:
            esp_real = st.number_input("Espessura Parede (cm)", 0.0, 2.0, 0.65, 0.01)

        f_col8, f_col9, f_col10 = st.columns(3)
        with f_col8:
            comp_real_medido = st.number_input(
                "Comprimento Seco Medido (cm):", 10.0, 50.0, float(comp_seco_sugerido), 0.1,
                help="Tamanho medido com paquimetro/trena no bloco seco."
            )
        with f_col9:
            peso_real = st.number_input("Peso Real Medido (kg)", 0.0, 15.0, 3.100, 0.001)
        with f_col10:
            obs_texto = st.text_area("Observacoes:", "Teste de rotina")

        btn_salvar = st.form_submit_button("Salvar Registro e Unificar Base", type="primary", use_container_width=True)

        if btn_salvar:
            tot_a_l = max(1, p_a + a_a + b_a)
            tot_b_l = max(1, p_b + a_b + b_b)
            pct_p_l = ((p_a / tot_a_l) + (p_b / tot_b_l)) / 2
            pct_a_l = ((a_a / tot_a_l) + (a_b / tot_b_l)) / 2
            pct_b_l = ((b_a / tot_a_l) + (b_b / tot_b_l)) / 2

            class_res_l = "fraco" if residuo_real > 32 else ("forte" if residuo_real < 28 else "ideal")
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

            persistir_dados("lotes")

            st.success("Lote registrado com sucesso com o Comprimento Seco Medido!")

            msg_wa_reg = (
                f"CeramicaIA — Registro de Lab Real\n\n"
                f"Data: {data_lote.strftime('%d/%m/%Y')} | Produto: {codigo_selecionado}\n"
                f"Barro Preto: {cod_p_reg} | Branco: {cod_b_reg}\n"
                f"MENSURACOES REAIS:\n"
                f"- Residuo: {residuo_real}% ({class_res_l.upper()})\n"
                f"- Umidade: {umidade_real}% | Retracao: {retracao_real}%\n"
                f"- Comp. Seco: {comp_real_medido:.1f} cm | Espessura: {esp_real} cm\n"
                f"- Peso Real: {peso_real:.3f} kg ({excesso_l:+.0f}g vs meta)\n\n"
                f"Obs: {obs_texto}"
            )

            wa_url_reg = f"https://wa.me/?text={urllib.parse.quote(msg_wa_reg)}"
            st.link_button("Compartilhar Teste de Lab no WhatsApp", wa_url_reg)

    st.divider()
    st.subheader(f"Base de Dados Completa da Fabrica ({len(st.session_state.df_master)} Lotes Totais)")
    st.dataframe(st.session_state.df_master, use_container_width=True)

    csv_completo = st.session_state.df_master.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="BAIXAR PLANILHA COMPLETA ATUALIZADA PARA RE-TREINO (CSV)",
        data=csv_completo,
        file_name=f"ceramica_lotes_completo_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True,
    )

# ============================================================
# ABA 3: ANALISE DE BARRO PURO (RECEBIMENTO DE CAMINHAO)
# ============================================================
with tab_puro:
    st.header("Controle de Qualidade na Entrada — Barro Puro (Jazida)")
    st.caption("Registre a quantidade de areia/residuo da materia-prima pura que chega dos caminhoes.")

    df_barros_ativos_puro = st.session_state.catalogo_barros[st.session_state.catalogo_barros["status"] == "Ativo"]
    lista_barros_puro = df_barros_ativos_puro["codigo"].tolist()

    col_puro1, col_puro2 = st.columns([1, 2])

    with col_puro1:
        st.subheader("Novo Teste de Barro Puro")
        with st.form("form_barro_puro", clear_on_submit=True):
            data_puro = st.date_input("Data da Amostra", datetime.now())
            cod_puro_sel = st.selectbox(
                "Selecione o Barro Puro:",
                lista_barros_puro if lista_barros_puro else ["01_BR_ARG_PRETO_SV"],
            )

            peso_amostra = st.number_input("Peso da Amostra Seca (g):", min_value=1.0, max_value=1000.0, value=100.0, step=10.0)
            peso_residuo_puro = st.number_input("Peso do Residuo Seco Retido (g):", min_value=0.0, max_value=500.0, value=35.0, step=1.0)

            pct_calculada = (peso_residuo_puro / peso_amostra) * 100 if peso_amostra > 0 else 0
            st.info(f"**Residuo do Barro Puro:** {pct_calculada:.1f}%")

            obs_puro = st.text_area("Observacoes (Lote/Caminhao):", "Caminhao 01 - Jazida Nova")

            btn_salvar_puro = st.form_submit_button("Salvar Laudo do Barro Puro", type="primary", use_container_width=True)

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

                persistir_dados("puro")

                st.success(f"Laudo do Barro `{cod_puro_sel}` ({pct_calculada:.1f}% residuo) registrado!")

    with col_puro2:
        st.subheader("Historico de Qualidade dos Barros Puros (Jazida)")
        if len(st.session_state.analises_puro) > 0:
            st.dataframe(st.session_state.analises_puro, use_container_width=True)
        else:
            st.info("Nenhum teste de barro puro registrado ainda nesta sessao.")

# ============================================================
# ABA 4: CADASTRO E GESTAO DE BARROS / JAZIDAS
# ============================================================
with tab_barros:
    st.header("Cadastro e Controle de Barros / Jazidas")
    st.caption("Cadastre novas jazidas, edite informacoes ou inative barros esgotados.")

    col_cad1, col_cad2 = st.columns(2)

    with col_cad1:
        st.subheader("Cadastrar Novo Barro")
        with st.form("form_novo_barro", clear_on_submit=True):
            novo_cod = st.text_input("Codigo Oficial (ex: 04_BR_ARG_PRETO_JAZIDA2):")
            novo_nome = st.text_input("Nome / Apelido Comercial:")
            novo_tipo = st.selectbox("Tipo Base para IA:", ["Preto", "Amarelo", "Branco"])
            nova_loc = st.text_input("Localidade / Jazida:")

            btn_cad_barro = st.form_submit_button("Cadastrar Barro", type="primary", use_container_width=True)

            if btn_cad_barro:
                if novo_cod and novo_nome:
                    cod_clean = novo_cod.strip().upper()
                    if cod_clean in st.session_state.catalogo_barros["codigo"].values:
                        st.error(f"O codigo `{cod_clean}` ja esta cadastrado!")
                    else:
                        novo_barro_dict = {
                            "codigo": cod_clean,
                            "nome": novo_nome.strip(),
                            "tipo_base": novo_tipo,
                            "localidade": nova_loc.strip(),
                            "status": "Ativo",
                        }
                        st.session_state.catalogo_barros = pd.concat(
                            [st.session_state.catalogo_barros, pd.DataFrame([novo_barro_dict])],
                            ignore_index=True,
                        )
                        persistir_dados("barros")
                        st.success(f"Barro `{cod_clean}` cadastrado!")
                        st.rerun()
                else:
                    st.error("Preencha o Codigo e o Nome do Barro.")

    with col_cad2:
        st.subheader("Editar Barro / Jazida Existente")
        lista_barros_cod = st.session_state.catalogo_barros["codigo"].tolist()

        if len(lista_barros_cod) > 0:
            barro_edit_sel = st.selectbox("Selecione o Barro para Editar:", lista_barros_cod)
            dados_atual = st.session_state.catalogo_barros[
                st.session_state.catalogo_barros["codigo"] == barro_edit_sel
            ].iloc[0]

            with st.form("form_editar_barro"):
                edit_cod = st.text_input("Codigo Oficial (Editar se necessario):", value=dados_atual["codigo"])
                edit_nome = st.text_input("Nome / Apelido:", value=dados_atual["nome"])
                lista_tipos = ["Preto", "Amarelo", "Branco"]
                idx_tipo = lista_tipos.index(dados_atual["tipo_base"]) if dados_atual["tipo_base"] in lista_tipos else 0
                edit_tipo = st.selectbox("Tipo Base para IA:", lista_tipos, index=idx_tipo)
                edit_loc = st.text_input("Localidade / Jazida:", value=dados_atual["localidade"])
                lista_status = ["Ativo", "Inativo"]
                idx_status = lista_status.index(dados_atual["status"]) if dados_atual["status"] in lista_status else 0
                edit_status = st.selectbox("Status no Sistema:", lista_status, index=idx_status)

                btn_salvar_edit = st.form_submit_button("Salvar Alteracoes", type="primary", use_container_width=True)

                if btn_salvar_edit:
                    idx_muda = st.session_state.catalogo_barros[
                        st.session_state.catalogo_barros["codigo"] == barro_edit_sel
                    ].index[0]

                    edit_cod_clean = edit_cod.strip().upper()

                    if not edit_cod_clean:
                        st.error("O codigo do barro nao pode ser vazio.")
                    elif edit_cod_clean != barro_edit_sel and edit_cod_clean in st.session_state.catalogo_barros["codigo"].values:
                        st.error(f"O codigo `{edit_cod_clean}` ja existe em outro cadastro!")
                    else:
                        if edit_cod_clean != barro_edit_sel:
                            for col in ["cod_barro_preto", "cod_barro_amarelo", "cod_barro_branco"]:
                                st.session_state.df_master[col] = st.session_state.df_master[col].replace(barro_edit_sel, edit_cod_clean)
                            persistir_dados("lotes")

                            st.session_state.analises_puro["codigo_barro"] = st.session_state.analises_puro["codigo_barro"].replace(barro_edit_sel, edit_cod_clean)
                            persistir_dados("puro")

                        st.session_state.catalogo_barros.at[idx_muda, "codigo"] = edit_cod_clean
                        st.session_state.catalogo_barros.at[idx_muda, "nome"] = edit_nome.strip()
                        st.session_state.catalogo_barros.at[idx_muda, "tipo_base"] = edit_tipo
                        st.session_state.catalogo_barros.at[idx_muda, "localidade"] = edit_loc.strip()
                        st.session_state.catalogo_barros.at[idx_muda, "status"] = edit_status

                        persistir_dados("barros")
                        st.success("Barro atualizado e referencias corrigidas em cascata!")
                        st.rerun()

    st.divider()
    st.subheader("Tabela Geral de Barros Cadastrados")
    st.dataframe(st.session_state.catalogo_barros, use_container_width=True)

# ============================================================
# ABA 5: CADASTRO E GESTAO DE PRODUTOS / BLOCOS
# ============================================================
with tab_produtos:
    st.header("Cadastro e Controle de Produtos / Blocos")
    st.caption("Adicione novos produtos do seu portfolio de vendas, ajuste as metas de peso padrao, dimensoes e comprimento de corte.")

    col_prod1, col_prod2 = st.columns(2)

    with col_prod1:
        st.subheader("Cadastrar Novo Produto")
        with st.form("form_novo_produto", clear_on_submit=True):
            n_prod_cod = st.text_input("Codigo do Bloco (ex: BP14, 01-BLP):")
            n_prod_nome = st.text_input("Descricao Comercial (ex: Bloco 8 Furos 9x19x19):")

            c_dim1, c_dim2, c_dim3 = st.columns(3)
            with c_dim1:
                n_prod_larg = st.number_input("Largura (cm):", 5.0, 30.0, 9.0, 0.5)
            with c_dim2:
                n_prod_comp_nom = st.number_input("Comprimento Nominal pos-queima (cm):", 5.0, 50.0, 19.0, 0.5)
            with c_dim3:
                n_prod_comp_sec = st.number_input("Comprimento Seco Ideal de Corte (cm):", 5.0, 55.0, 20.0, 0.5)

            n_prod_peso = st.number_input("Meta de Peso Padrao (kg):", 0.500, 15.000, 2.800, 0.050, format="%.3f")

            btn_cad_prod = st.form_submit_button("Cadastrar Produto", type="primary", use_container_width=True)

            if btn_cad_prod:
                if n_prod_cod and n_prod_nome:
                    prod_cod_clean = n_prod_cod.strip().upper()
                    if prod_cod_clean in st.session_state.catalogo_produtos["codigo"].values:
                        st.error(f"O codigo `{prod_cod_clean}` ja esta cadastrado!")
                    else:
                        nova_chave = f"{prod_cod_clean} ({n_prod_larg:.0f}x{n_prod_comp_nom:.0f}x{n_prod_comp_nom:.0f} cm) — {n_prod_nome.strip()}"
                        novo_prod_dict = {
                            "chave_comercial": nova_chave,
                            "codigo": prod_cod_clean,
                            "largura": n_prod_larg,
                            "comprimento_nominal": n_prod_comp_nom,
                            "comp_seco_ideal": n_prod_comp_sec,
                            "peso_padrao": n_prod_peso,
                            "status": "Ativo",
                        }

                        st.session_state.catalogo_produtos = pd.concat(
                            [st.session_state.catalogo_produtos, pd.DataFrame([novo_prod_dict])],
                            ignore_index=True,
                        )
                        persistir_dados("produtos")
                        st.success(f"Produto `{prod_cod_clean}` cadastrado!")
                        st.rerun()
                else:
                    st.error("Preencha o Codigo e a Descricao Comercial.")

    with col_prod2:
        st.subheader("Editar Produto Existente")
        lista_produtos_cod = st.session_state.catalogo_produtos["codigo"].tolist()

        if len(lista_produtos_cod) > 0:
            prod_edit_sel = st.selectbox("Selecione o Produto para Editar:", lista_produtos_cod)
            dados_prod_atual = st.session_state.catalogo_produtos[
                st.session_state.catalogo_produtos["codigo"] == prod_edit_sel
            ].iloc[0]

            with st.form("form_editar_produto"):
                edit_prod_cod = st.text_input("Codigo do Produto (Editar se necessario):", value=dados_prod_atual["codigo"])
                try:
                    descricao_atual = dados_prod_atual["chave_comercial"].split(" — ")[-1]
                except Exception:
                    descricao_atual = dados_prod_atual["chave_comercial"]

                edit_prod_nome = st.text_input("Descricao Comercial:", value=descricao_atual)

                ce_dim1, ce_dim2, ce_dim3 = st.columns(3)
                with ce_dim1:
                    edit_prod_larg = st.number_input("Largura (cm):", 5.0, 30.0, float(dados_prod_atual["largura"]), 0.5)
                with ce_dim2:
                    edit_prod_comp_nom = st.number_input("Comprimento Nominal pos-queima (cm):", 5.0, 50.0, float(dados_prod_atual["comprimento_nominal"]), 0.5)
                with ce_dim3:
                    edit_prod_comp_sec = st.number_input("Comprimento Seco Ideal de Corte (cm):", 5.0, 55.0, float(dados_prod_atual["comp_seco_ideal"]), 0.5)

                edit_prod_peso = st.number_input("Meta de Peso Padrao (kg):", 0.500, 15.000, float(dados_prod_atual["peso_padrao"]), 0.050, format="%.3f")

                lista_status_p = ["Ativo", "Inativo"]
                idx_status_p = lista_status_p.index(dados_prod_atual["status"]) if dados_prod_atual["status"] in lista_status_p else 0
                edit_prod_status = st.selectbox("Status do Produto:", lista_status_p, index=idx_status_p)

                btn_salvar_prod_edit = st.form_submit_button("Salvar Alteracoes de Produto", type="primary", use_container_width=True)

                if btn_salvar_prod_edit:
                    idx_prod_muda = st.session_state.catalogo_produtos[
                        st.session_state.catalogo_produtos["codigo"] == prod_edit_sel
                    ].index[0]

                    edit_prod_cod_clean = edit_prod_cod.strip().upper()

                    if not edit_prod_cod_clean:
                        st.error("O codigo do produto nao pode ser vazio.")
                    elif edit_prod_cod_clean != prod_edit_sel and edit_prod_cod_clean in st.session_state.catalogo_produtos["codigo"].values:
                        st.error(f"O codigo `{edit_prod_cod_clean}` ja existe em outro produto!")
                    else:
                        if edit_prod_cod_clean != prod_edit_sel:
                            st.session_state.df_master["tipo_bloco"] = st.session_state.df_master["tipo_bloco"].replace(prod_edit_sel, edit_prod_cod_clean)
                            persistir_dados("lotes")

                        nova_chave_edit = f"{edit_prod_cod_clean} ({edit_prod_larg:.0f}x{edit_prod_comp_nom:.0f}x{edit_prod_comp_nom:.0f} cm) — {edit_prod_nome.strip()}"

                        st.session_state.catalogo_produtos.at[idx_prod_muda, "codigo"] = edit_prod_cod_clean
                        st.session_state.catalogo_produtos.at[idx_prod_muda, "chave_comercial"] = nova_chave_edit
                        st.session_state.catalogo_produtos.at[idx_prod_muda, "largura"] = edit_prod_larg
                        st.session_state.catalogo_produtos.at[idx_prod_muda, "comprimento_nominal"] = edit_prod_comp_nom
                        st.session_state.catalogo_produtos.at[idx_prod_muda, "comp_seco_ideal"] = edit_prod_comp_sec
                        st.session_state.catalogo_produtos.at[idx_prod_muda, "peso_padrao"] = edit_prod_peso
                        st.session_state.catalogo_produtos.at[idx_prod_muda, "status"] = edit_prod_status

                        persistir_dados("produtos")
                        st.success("Produto atualizado e referencias corrigidas em cascata!")
                        st.rerun()

    st.divider()
    st.subheader("Tabela Geral de Produtos / Blocos Cadastrados")
    st.dataframe(st.session_state.catalogo_produtos, use_container_width=True)
