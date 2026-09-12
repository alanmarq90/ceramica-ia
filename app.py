# ============================================================
# CERAMICAIA v15.0
# IA DE RESIDUO 100% BASEADA NOS LOTES REAIS
# Barro puro mantido apenas para acompanhamento
# ============================================================

import os
import urllib.parse
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

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
    page_title="CeramicaIA - Gestao de Barros e Misturas",
    page_icon="logo.png" if os.path.exists("logo.png") else None,
    layout="wide",
)

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

    .status-erro {
        background-color: #f8d7da;
        color: #721c24;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
    st.sidebar.markdown("---")

st.markdown(
    '<div class="main-header">CeramicaIA - Otimizador de Misturas e Rastreabilidade</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-header">Previsao por aprendizado dos lotes reais, controle dimensional, gestao de barros e calculo de perdas</div>',
    unsafe_allow_html=True,
)

st.divider()


# ============================================================
# CONEXAO GOOGLE SHEETS
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

        creds = Credentials.from_service_account_info(
            gcp_creds_dict,
            scopes=scopes,
        )

        client = gspread.authorize(creds)

        spreadsheet = client.open_by_key(gsheet_id)

        worksheet_lotes = spreadsheet.worksheet("lotes")
        worksheet_barros = spreadsheet.worksheet("barros")
        worksheet_produtos = spreadsheet.worksheet("produtos")
        worksheet_puro = spreadsheet.worksheet("analises_puro")

        MODO_SHEETS = True

    except Exception as e:

        st.sidebar.markdown(
            f'<div class="status-local">Banco de dados: CSV Local<br>Aviso: {str(e)[:80]}</div>',
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
# FUNCOES GOOGLE SHEETS
# ============================================================

def ler_dados_sheets(worksheet, colunas):

    try:

        dados = worksheet.get_all_records()

        if dados:
            df = pd.DataFrame(dados)

            for col in colunas:
                if col not in df.columns:
                    df[col] = np.nan

            return df

    except Exception:
        pass

    return pd.DataFrame(columns=colunas)


def salvar_no_sheets(worksheet, df):

    try:

        worksheet.clear()

        df_str = df.fillna("").astype(str)

        dados_lista = [
            df_str.columns.tolist()
        ] + df_str.values.tolist()

        worksheet.update(dados_lista)

    except Exception as e:

        st.error(
            f"Erro ao sincronizar com Google Sheets: {e}"
        )


# ============================================================
# ESTRUTURA DOS BANCOS
# ============================================================

COLUNAS_BARROS = [
    "codigo",
    "nome",
    "tipo_base",
    "localidade",
    "residuo_puro",
    "status",
]

COLUNAS_PRODUTOS = [
    "chave_comercial",
    "codigo",
    "largura",
    "comprimento_nominal",
    "comp_seco_ideal",
    "peso_padrao",
    "status",
]

COLUNAS_LOTES = [
    "data",
    "modo",
    "cod_barro_preto",
    "cod_barro_amarelo",
    "cod_barro_branco",
    "preto_a",
    "amarelo_a",
    "branco_a",
    "preto_b",
    "amarelo_b",
    "branco_b",
    "pct_preto",
    "pct_amarelo",
    "pct_branco",
    "umidade",
    "residuo",
    "retracao",
    "esp_parede",
    "peso",
    "comprimento",
    "tipo_bloco",
    "class_residuo",
    "excesso_peso",
    "observacoes",
]

COLUNAS_PURO = [
    "data",
    "codigo_barro",
    "peso_amostra_g",
    "peso_residuo_g",
    "pct_residuo_puro",
    "observacoes",
]


# ============================================================
# DADOS PADRAO SOMENTE PARA CADASTRO
# NAO SAO USADOS PARA TREINAR RESIDUO
# ============================================================

BARROS_INICIAIS = [
    {
        "codigo": "01_BR_ARG_PRETO_SV",
        "nome": "Barro Argiloso Preto (Sao Vicente)",
        "tipo_base": "Preto",
        "localidade": "Sao Vicente (SV)",
        "residuo_puro": 0.0,
        "status": "Ativo",
    },
    {
        "codigo": "02_BR_ARG_AMAREL_STPREZ",
        "nome": "Barro Amarelo (Sitio Prazeres)",
        "tipo_base": "Amarelo",
        "localidade": "Sitio Prazeres (STPRAZ)",
        "residuo_puro": 0.0,
        "status": "Ativo",
    },
    {
        "codigo": "03_BR_AREN_BRANCO_STPRAZ",
        "nome": "Barro Arenoso Branco (Sitio Prazeres)",
        "tipo_base": "Branco",
        "localidade": "Sitio Prazeres (STPRAZ)",
        "residuo_puro": 0.0,
        "status": "Ativo",
    },
]


PRODUTOS_INICIAIS = [
    {
        "chave_comercial": "01-BLP (9x19x19 cm) - Vedacao Padrao",
        "codigo": "01-BLP",
        "largura": 9.0,
        "comprimento_nominal": 19.0,
        "comp_seco_ideal": 20.0,
        "peso_padrao": 2.800,
        "status": "Ativo",
    },
    {
        "chave_comercial": "BP14 (14x19x19 cm) - Estrutural Curto",
        "codigo": "BP14",
        "largura": 14.0,
        "comprimento_nominal": 19.0,
        "comp_seco_ideal": 20.0,
        "peso_padrao": 3.800,
        "status": "Ativo",
    },
    {
        "chave_comercial": "02-BLG (9x19x39 cm) - Bloco Grande / Canaleta 9",
        "codigo": "02-BLG",
        "largura": 9.0,
        "comprimento_nominal": 39.0,
        "comp_seco_ideal": 40.0,
        "peso_padrao": 5.500,
        "status": "Ativo",
    },
    {
        "chave_comercial": "BG14 (14x19x39 cm) - Estrutural Grande 14",
        "codigo": "BG14",
        "largura": 14.0,
        "comprimento_nominal": 39.0,
        "comp_seco_ideal": 40.0,
        "peso_padrao": 7.000,
        "status": "Ativo",
    },
]


# ============================================================
# CARREGAMENTO
# GOOGLE SHEETS E A FONTE PRINCIPAL
# ============================================================

if "catalogo_barros" not in st.session_state:

    if MODO_SHEETS:

        df_b = ler_dados_sheets(
            worksheet_barros,
            COLUNAS_BARROS,
        )

        if len(df_b) == 0:

            df_b = pd.DataFrame(BARROS_INICIAIS)
            salvar_no_sheets(worksheet_barros, df_b)

        st.session_state.catalogo_barros = df_b

    elif os.path.exists("db_catalogo_barros.csv"):

        st.session_state.catalogo_barros = pd.read_csv(
            "db_catalogo_barros.csv"
        )

    else:

        st.session_state.catalogo_barros = pd.DataFrame(
            BARROS_INICIAIS
        )


if "catalogo_produtos" not in st.session_state:

    if MODO_SHEETS:

        df_p = ler_dados_sheets(
            worksheet_produtos,
            COLUNAS_PRODUTOS,
        )

        if len(df_p) == 0:

            df_p = pd.DataFrame(PRODUTOS_INICIAIS)
            salvar_no_sheets(
                worksheet_produtos,
                df_p,
            )

        st.session_state.catalogo_produtos = df_p

    elif os.path.exists("db_catalogo_produtos.csv"):

        st.session_state.catalogo_produtos = pd.read_csv(
            "db_catalogo_produtos.csv"
        )

    else:

        st.session_state.catalogo_produtos = pd.DataFrame(
            PRODUTOS_INICIAIS
        )


if "df_master" not in st.session_state:

    if MODO_SHEETS:

        df_l = ler_dados_sheets(
            worksheet_lotes,
            COLUNAS_LOTES,
        )

        st.session_state.df_master = df_l

    elif os.path.exists("db_df_master.csv"):

        st.session_state.df_master = pd.read_csv(
            "db_df_master.csv"
        )

    else:

        st.session_state.df_master = pd.DataFrame(
            columns=COLUNAS_LOTES
        )


if "analises_puro" not in st.session_state:

    if MODO_SHEETS:

        st.session_state.analises_puro = ler_dados_sheets(
            worksheet_puro,
            COLUNAS_PURO,
        )

    elif os.path.exists("db_analises_puro.csv"):

        st.session_state.analises_puro = pd.read_csv(
            "db_analises_puro.csv"
        )

    else:

        st.session_state.analises_puro = pd.DataFrame(
            columns=COLUNAS_PURO
        )


if "diagnostico_gerado" not in st.session_state:
    st.session_state.diagnostico_gerado = False


if "versao_dados" not in st.session_state:
    st.session_state.versao_dados = 0


# ============================================================
# PERSISTENCIA
# ============================================================

def marcar_dados_alterados():

    st.session_state.versao_dados += 1


def persistir_dados(tipo):

    if tipo == "barros":

        df = st.session_state.catalogo_barros

        if MODO_SHEETS:
            salvar_no_sheets(
                worksheet_barros,
                df,
            )

        try:
            df.to_csv(
                "db_catalogo_barros.csv",
                index=False,
            )
        except Exception:
            pass

    elif tipo == "produtos":

        df = st.session_state.catalogo_produtos

        if MODO_SHEETS:
            salvar_no_sheets(
                worksheet_produtos,
                df,
            )

        try:
            df.to_csv(
                "db_catalogo_produtos.csv",
                index=False,
            )
        except Exception:
            pass

    elif tipo == "lotes":

        df = st.session_state.df_master

        if MODO_SHEETS:
            salvar_no_sheets(
                worksheet_lotes,
                df,
            )

        try:
            df.to_csv(
                "db_df_master.csv",
                index=False,
            )
        except Exception:
            pass

    elif tipo == "puro":

        df = st.session_state.analises_puro

        if MODO_SHEETS:
            salvar_no_sheets(
                worksheet_puro,
                df,
            )

        try:
            df.to_csv(
                "db_analises_puro.csv",
                index=False,
            )
        except Exception:
            pass

    marcar_dados_alterados()


# ============================================================
# CALCULO CORRETO DAS RECEITAS
# ============================================================

def calcular_percentuais_receita(
    modo,
    p_a,
    a_a,
    b_a,
    p_b,
    a_b,
    b_b,
):

    if str(modo).lower().startswith("unica") or str(modo).lower().startswith("receita unica"):

        total = p_a + a_a + b_a

        if total <= 0:
            return 0.0, 0.0, 0.0

        return (
            p_a / total,
            a_a / total,
            b_a / total,
        )

    # Mesclada A, B, A, B...
    # Soma real das conchas dos dois ciclos

    total_preto = p_a + p_b
    total_amarelo = a_a + a_b
    total_branco = b_a + b_b

    total = (
        total_preto
        + total_amarelo
        + total_branco
    )

    if total <= 0:
        return 0.0, 0.0, 0.0

    return (
        total_preto / total,
        total_amarelo / total,
        total_branco / total,
    )


# ============================================================
# PREPARACAO DA BASE
# ============================================================

def montar_dataset_treino(
    df_lotes,
    df_produtos,
):

    if df_lotes is None or len(df_lotes) == 0:
        return pd.DataFrame()

    df = df_lotes.copy()

    colunas_numericas = [
        "preto_a",
        "amarelo_a",
        "branco_a",
        "preto_b",
        "amarelo_b",
        "branco_b",
        "umidade",
        "residuo",
        "retracao",
        "esp_parede",
        "peso",
        "comprimento",
    ]

    for col in colunas_numericas:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )


    # ----------------------------------------------
    # RECALCULA PERCENTUAIS DIRETO DAS CONCHAS
    # SEM ALTERAR O GOOGLE SHEETS
    # ----------------------------------------------

    pct_preto_corr = []
    pct_amarelo_corr = []
    pct_branco_corr = []

    for _, row in df.iterrows():

        p_a = float(row.get("preto_a", 0) or 0)
        a_a = float(row.get("amarelo_a", 0) or 0)
        b_a = float(row.get("branco_a", 0) or 0)

        p_b = float(row.get("preto_b", p_a) or 0)
        a_b = float(row.get("amarelo_b", a_a) or 0)
        b_b = float(row.get("branco_b", b_a) or 0)

        modo = str(row.get("modo", "Unica"))

        pp, pa, pb = calcular_percentuais_receita(
            modo,
            p_a,
            a_a,
            b_a,
            p_b,
            a_b,
            b_b,
        )

        pct_preto_corr.append(pp)
        pct_amarelo_corr.append(pa)
        pct_branco_corr.append(pb)


    df["pct_preto_ia"] = pct_preto_corr
    df["pct_amarelo_ia"] = pct_amarelo_corr
    df["pct_branco_ia"] = pct_branco_corr


    # ----------------------------------------------
    # DATA
    # ----------------------------------------------

    df["data_dt"] = pd.to_datetime(
        df["data"],
        errors="coerce",
    )


    # ----------------------------------------------
    # PRODUTO / PESO
    # ----------------------------------------------

    try:

        mapa_largura = dict(
            zip(
                df_produtos["codigo"],
                pd.to_numeric(
                    df_produtos["largura"],
                    errors="coerce",
                ),
            )
        )

        df["largura_cm"] = df["tipo_bloco"].map(
            mapa_largura
        )

    except Exception:

        df["largura_cm"] = np.nan


    df["comprimento_cm"] = pd.to_numeric(
        df["comprimento"],
        errors="coerce",
    )

    return df


# ============================================================
# MODELOS
# ============================================================

FEATURES_PESO = [
    "esp_parede",
    "largura_cm",
    "comprimento_cm",
    "umidade",
]

# Parede foi retirada do RESIDUO.
# Preto tambem nao precisa entrar porque:
# Preto + Amarelo + Branco = 100%.
FEATURES_RESIDUO = [
    "pct_amarelo_ia",
    "pct_branco_ia",
    "umidade",
]

FEATURES_RETRACAO = [
    "pct_preto_ia",
    "pct_amarelo_ia",
    "pct_branco_ia",
    "umidade",
    "esp_parede",
]


# ============================================================
# PESOS TEMPORAIS
# DADOS NOVOS TEM MAIS IMPORTANCIA
# ============================================================

def calcular_pesos_temporais(datas):

    datas = pd.to_datetime(
        datas,
        errors="coerce",
    )

    if datas.notna().sum() == 0:
        return np.ones(len(datas))

    data_max = datas.max()

    idade_dias = (
        data_max - datas
    ).dt.days.fillna(365)

    # Meia vida aproximada de 180 dias.
    # Lotes recentes recebem mais importancia,
    # mas dados antigos nao sao descartados.

    pesos = np.exp(
        -idade_dias / 180.0
    )

    # Evita peso praticamente zero

    pesos = np.maximum(
        pesos,
        0.10,
    )

    return np.asarray(pesos)


# ============================================================
# TREINAMENTO
# ============================================================

def treinar_modelos_ia(
    df_lotes,
    df_produtos,
):

    df = montar_dataset_treino(
        df_lotes,
        df_produtos,
    )

    n_total = len(df)

    metricas = {
        "n": n_total,
        "n_residuo": 0,
        "r2_peso": None,
        "r2_residuo_treino": None,
        "mae_residuo_validacao": None,
        "r2_retracao": None,
    }

    if n_total < 5:

        return (
            None,
            None,
            None,
            metricas,
            df,
        )


    # ========================================================
    # MODELO PESO
    # ========================================================

    df_peso = df.dropna(
        subset=FEATURES_PESO + ["peso"]
    )

    m_peso = None

    if len(df_peso) >= 5:

        X_peso = df_peso[
            FEATURES_PESO
        ].astype(float)

        y_peso = df_peso[
            "peso"
        ].astype(float)

        m_peso = GradientBoostingRegressor(
            random_state=42,
            n_estimators=120,
            learning_rate=0.04,
            max_depth=2,
            loss="huber",
        )

        m_peso.fit(
            X_peso,
            y_peso,
        )

        try:

            metricas["r2_peso"] = round(
                float(
                    r2_score(
                        y_peso,
                        m_peso.predict(X_peso),
                    )
                ),
                3,
            )

        except Exception:
            pass


    # ========================================================
    # MODELO RESIDUO
    # DIRETO, SEM BARRO PURO
    # ========================================================

    df_res = df.dropna(
        subset=FEATURES_RESIDUO + ["residuo", "data_dt"]
    ).copy()

    df_res = df_res.sort_values(
        "data_dt"
    )

    metricas["n_residuo"] = len(df_res)

    m_res = None


    if len(df_res) >= 10:

        X_res = df_res[
            FEATURES_RESIDUO
        ].astype(float)

        y_res = df_res[
            "residuo"
        ].astype(float)

        pesos = calcular_pesos_temporais(
            df_res["data_dt"]
        )

        m_res = GradientBoostingRegressor(
            random_state=42,
            n_estimators=100,
            learning_rate=0.035,
            max_depth=2,
            min_samples_leaf=4,
            loss="huber",
        )

        m_res.fit(
            X_res,
            y_res,
            sample_weight=pesos,
        )


        try:

            pred_treino = m_res.predict(
                X_res
            )

            metricas["r2_residuo_treino"] = round(
                float(
                    r2_score(
                        y_res,
                        pred_treino,
                    )
                ),
                3,
            )

        except Exception:
            pass


        # ====================================================
        # VALIDACAO TEMPORAL
        # TREINA COM PASSADO E TESTA NOS ULTIMOS LOTES
        # ====================================================

        if len(df_res) >= 20:

            qtd_teste = max(
                5,
                int(len(df_res) * 0.20),
            )

            treino = df_res.iloc[:-qtd_teste].copy()
            teste = df_res.iloc[-qtd_teste:].copy()

            X_train = treino[
                FEATURES_RESIDUO
            ].astype(float)

            y_train = treino[
                "residuo"
            ].astype(float)

            X_test = teste[
                FEATURES_RESIDUO
            ].astype(float)

            y_test = teste[
                "residuo"
            ].astype(float)

            pesos_train = calcular_pesos_temporais(
                treino["data_dt"]
            )

            m_validacao = GradientBoostingRegressor(
                random_state=42,
                n_estimators=100,
                learning_rate=0.035,
                max_depth=2,
                min_samples_leaf=4,
                loss="huber",
            )

            m_validacao.fit(
                X_train,
                y_train,
                sample_weight=pesos_train,
            )

            pred_test = m_validacao.predict(
                X_test
            )

            metricas["mae_residuo_validacao"] = round(
                float(
                    mean_absolute_error(
                        y_test,
                        pred_test,
                    )
                ),
                2,
            )


    # ========================================================
    # RETRACAO
    # ========================================================

    df_ret = df.dropna(
        subset=FEATURES_RETRACAO + ["retracao"]
    )

    m_ret = None

    if len(df_ret) >= 5:

        X_ret = df_ret[
            FEATURES_RETRACAO
        ].astype(float)

        y_ret = df_ret[
            "retracao"
        ].astype(float)

        m_ret = GradientBoostingRegressor(
            random_state=42,
            n_estimators=100,
            learning_rate=0.04,
            max_depth=2,
            loss="huber",
        )

        m_ret.fit(
            X_ret,
            y_ret,
        )

        try:

            metricas["r2_retracao"] = round(
                float(
                    r2_score(
                        y_ret,
                        m_ret.predict(X_ret),
                    )
                ),
                3,
            )

        except Exception:
            pass


    return (
        m_peso,
        m_res,
        m_ret,
        metricas,
        df,
    )


# ============================================================
# TREINA / RETREINA
# ============================================================

if (
    "modelos_ia" not in st.session_state
    or st.session_state.get("versao_treinada")
    != st.session_state.versao_dados
):

    with st.spinner(
        "Calibrando IA com os lotes reais da fabrica..."
    ):

        (
            m_pes,
            m_res,
            m_ret,
            metricas_ia,
            df_treino_ia,
        ) = treinar_modelos_ia(
            st.session_state.df_master,
            st.session_state.catalogo_produtos,
        )

        st.session_state.modelos_ia = (
            m_pes,
            m_res,
            m_ret,
        )

        st.session_state.metricas_ia = metricas_ia
        st.session_state.df_treino_ia = df_treino_ia

        st.session_state.versao_treinada = (
            st.session_state.versao_dados
        )

else:

    (
        m_pes,
        m_res,
        m_ret,
    ) = st.session_state.modelos_ia

    metricas_ia = (
        st.session_state.metricas_ia
    )

    df_treino_ia = (
        st.session_state.df_treino_ia
    )


if m_res is None:

    st.error(
        "Ainda nao existem dados suficientes para treinar "
        "a IA de residuo."
    )

    st.stop()


st.sidebar.markdown(
    f'<div class="status-ok">IA treinada com {metricas_ia["n_residuo"]} analises de residuo</div>',
    unsafe_allow_html=True,
)


with st.sidebar.expander(
    "Detalhes do treinamento da IA"
):

    st.write(
        f"Lotes totais: {metricas_ia['n']}"
    )

    st.write(
        f"Lotes usados no Residuo: {metricas_ia['n_residuo']}"
    )

    st.write(
        f"R2 Residuo (treino): {metricas_ia['r2_residuo_treino']}"
    )

    if metricas_ia["mae_residuo_validacao"] is not None:

        st.write(
            f"Erro medio em dados futuros simulados: "
            f"{metricas_ia['mae_residuo_validacao']:.2f} pontos %"
        )

    st.write(
        f"R2 Peso: {metricas_ia['r2_peso']}"
    )

    st.write(
        f"R2 Retracao: {metricas_ia['r2_retracao']}"
    )

    st.caption(
        "Residuo aprende somente com analises reais dos blocos. "
        "Analises de barro puro nao interferem nesta previsao."
    )


# ============================================================
# PREVISAO LOCAL / CASOS SEMELHANTES
# ============================================================

def encontrar_casos_semelhantes(
    df,
    pct_amarelo,
    pct_branco,
    umidade,
    limite=8,
):

    if df is None or len(df) == 0:
        return pd.DataFrame()

    base = df.dropna(
        subset=[
            "pct_amarelo_ia",
            "pct_branco_ia",
            "umidade",
            "residuo",
            "data_dt",
        ]
    ).copy()

    if len(base) == 0:
        return base


    # Distancia:
    # composicao pesa mais que umidade

    base["distancia_ia"] = (
        abs(
            base["pct_amarelo_ia"]
            - pct_amarelo
        ) * 100 * 1.5
        +
        abs(
            base["pct_branco_ia"]
            - pct_branco
        ) * 100 * 2.0
        +
        abs(
            base["umidade"]
            - umidade
        ) * 0.25
    )


    # Bonus para registros recentes

    data_max = base["data_dt"].max()

    base["idade_dias"] = (
        data_max - base["data_dt"]
    ).dt.days.clip(lower=0)

    base["score_vizinho"] = (
        base["distancia_ia"]
        +
        base["idade_dias"] / 180.0
    )

    base = base.sort_values(
        [
            "score_vizinho",
            "data_dt",
        ],
        ascending=[
            True,
            False,
        ],
    )

    return base.head(limite)


def prever_residuo_inteligente(
    modelo,
    df,
    pct_amarelo,
    pct_branco,
    umidade,
):

    X = pd.DataFrame(
        [
            {
                "pct_amarelo_ia": pct_amarelo,
                "pct_branco_ia": pct_branco,
                "umidade": umidade,
            }
        ]
    )

    pred_ml = float(
        modelo.predict(X)[0]
    )

    vizinhos = encontrar_casos_semelhantes(
        df,
        pct_amarelo,
        pct_branco,
        umidade,
        limite=8,
    )


    # Se houver casos realmente proximos,
    # combinamos IA geral + realidade local recente.

    if len(vizinhos) > 0:

        vizinhos_fortes = vizinhos[
            vizinhos["distancia_ia"] <= 3.0
        ].copy()

    else:

        vizinhos_fortes = pd.DataFrame()


    if len(vizinhos_fortes) >= 2:

        pesos_v = (
            1.0
            /
            (
                0.5
                + vizinhos_fortes["distancia_ia"]
            )
        )

        media_local = float(
            np.average(
                vizinhos_fortes["residuo"],
                weights=pesos_v,
            )
        )


        # Casos reais proximos recebem prioridade

        pred_final = (
            0.35 * pred_ml
            +
            0.65 * media_local
        )

        if len(vizinhos_fortes) >= 4:
            confianca = "ALTA"
        else:
            confianca = "MEDIA"

    else:

        media_local = None
        pred_final = pred_ml
        confianca = "BAIXA"


    return (
        pred_final,
        pred_ml,
        media_local,
        confianca,
        vizinhos,
    )


# ============================================================
# ABAS
# ============================================================

tab_diag, tab_reg, tab_puro, tab_barros, tab_produtos = st.tabs(
    [
        "Diagnostico e Previsao",
        "Registrar Analise de Mistura",
        "Analise de Barro Puro (Recebimento)",
        "Cadastrar / Gerenciar Barros",
        "Cadastrar / Gerenciar Produtos",
    ]
)


# ============================================================
# ABA 1 - DIAGNOSTICO
# ============================================================

with tab_diag:

    st.sidebar.header(
        "Configuracoes do Lote"
    )

    df_prod_ativos = (
        st.session_state.catalogo_produtos[
            st.session_state.catalogo_produtos["status"]
            == "Ativo"
        ]
    )

    if len(df_prod_ativos) == 0:

        st.error(
            "Nenhum produto ativo cadastrado."
        )

        st.stop()


    produto_sel = st.sidebar.selectbox(
        "Selecione o Produto em Producao:",
        df_prod_ativos[
            "chave_comercial"
        ].tolist(),
    )

    dados_prod = df_prod_ativos[
        df_prod_ativos["chave_comercial"]
        == produto_sel
    ].iloc[0]


    largura_cm = float(
        dados_prod["largura"]
    )

    comp_seco_ideal = float(
        dados_prod["comp_seco_ideal"]
    )

    peso_padrao = float(
        dados_prod["peso_padrao"]
    )

    codigo_prod = dados_prod["codigo"]

    comprimento_nominal = float(
        dados_prod["comprimento_nominal"]
    )


    st.sidebar.info(
        f"Meta de Peso Padrao: {peso_padrao:.3f} kg\n\n"
        f"Comprimento Verde Ideal: {comp_seco_ideal:.1f} cm"
    )


    st.header(
        "Selecao dos Barros Cadastrados"
    )

    df_barros_ativos = (
        st.session_state.catalogo_barros[
            st.session_state.catalogo_barros["status"]
            == "Ativo"
        ]
    )


    barros_pretos = (
        df_barros_ativos[
            df_barros_ativos["tipo_base"]
            == "Preto"
        ]["codigo"].tolist()
    )

    barros_amarelos = (
        ["Nenhum"]
        + df_barros_ativos[
            df_barros_ativos["tipo_base"]
            == "Amarelo"
        ]["codigo"].tolist()
    )

    barros_brancos = (
        ["Nenhum"]
        + df_barros_ativos[
            df_barros_ativos["tipo_base"]
            == "Branco"
        ]["codigo"].tolist()
    )


    col_b1, col_b2, col_b3 = st.columns(3)


    with col_b1:

        sel_barro_preto = st.selectbox(
            "Barro Argiloso (Forte):",
            barros_pretos
            if barros_pretos
            else ["01_BR_ARG_PRETO_SV"],
        )


    with col_b2:

        sel_barro_amarelo = st.selectbox(
            "Barro Intermediario (Medio):",
            barros_amarelos,
        )


    with col_b3:

        sel_barro_branco = st.selectbox(
            "Barro Arenoso (Fraco):",
            barros_brancos
            if len(barros_brancos) > 1
            else ["03_BR_AREN_BRANCO_STPRAZ"],
        )


    st.divider()

    st.header(
        "Composicao em Conchas"
    )


    modo = st.radio(
        "Tipo de Producao do Dia:",
        [
            "Receita Unica",
            "Mistura Mesclada (Alternada)",
        ],
        horizontal=True,
    )


    if modo == "Receita Unica":

        c1, c2, c3 = st.columns(3)

        with c1:

            preto_a = st.number_input(
                "Conchas de Preto",
                0,
                10,
                4,
                1,
            )

        with c2:

            amarelo_a = st.number_input(
                "Conchas de Amarelo",
                0,
                10,
                0 if sel_barro_amarelo == "Nenhum" else 1,
                1,
            )

        with c3:

            branco_a = st.number_input(
                "Conchas de Branco",
                0,
                10,
                1,
                1,
            )


        preto_b = preto_a
        amarelo_b = amarelo_a
        branco_b = branco_a


        pct_preto, pct_amarelo, pct_branco = (
            calcular_percentuais_receita(
                "Unica",
                preto_a,
                amarelo_a,
                branco_a,
                preto_b,
                amarelo_b,
                branco_b,
            )
        )


        mistura_desc = (
            f"{preto_a} Preto + "
            f"{amarelo_a} Amarelo + "
            f"{branco_a} Branco"
        )


    else:

        st.subheader(
            "Receita A"
        )

        c1, c2, c3 = st.columns(3)


        with c1:

            preto_a = st.number_input(
                "Preto (A)",
                0,
                10,
                3,
                1,
            )


        with c2:

            amarelo_a = st.number_input(
                "Amarelo (A)",
                0,
                10,
                1,
                1,
            )


        with c3:

            branco_a = st.number_input(
                "Branco (A)",
                0,
                10,
                1,
                1,
            )


        st.subheader(
            "Receita B"
        )

        c4, c5, c6 = st.columns(3)


        with c4:

            preto_b = st.number_input(
                "Preto (B)",
                0,
                10,
                3,
                1,
            )


        with c5:

            amarelo_b = st.number_input(
                "Amarelo (B)",
                0,
                10,
                1,
                1,
            )


        with c6:

            branco_b = st.number_input(
                "Branco (B)",
                0,
                10,
                2,
                1,
            )


        pct_preto, pct_amarelo, pct_branco = (
            calcular_percentuais_receita(
                "Mesclada",
                preto_a,
                amarelo_a,
                branco_a,
                preto_b,
                amarelo_b,
                branco_b,
            )
        )


        mistura_desc = (
            f"A({preto_a}/{amarelo_a}/{branco_a}) "
            f"+ B({preto_b}/{amarelo_b}/{branco_b})"
        )


    st.info(
        f"Composicao real pelas conchas: "
        f"{pct_preto*100:.2f}% Preto | "
        f"{pct_amarelo*100:.2f}% Amarelo | "
        f"{pct_branco*100:.2f}% Branco"
    )

    st.caption(
        "Na mistura Mesclada A,B,A,B, a porcentagem e calculada "
        "pela soma total das conchas dos dois ciclos."
    )


    st.divider()

    st.header(
        "Parametros de Processo e Dimensao de Corte"
    )

    col_u, col_e, col_c = st.columns(3)


    with col_u:

        umidade = st.number_input(
            "Umidade da Massa na Maromba (%)",
            5.0,
            30.0,
            16.0,
            0.5,
        )


    with col_e:

        esp_parede = st.number_input(
            "Espessura da Parede (cm)",
            0.20,
            1.50,
            0.65,
            0.01,
        )


    with col_c:

        comprimento_cm = st.number_input(
            "Comprimento Verde de Corte na Extrusora (cm):",
            15.0,
            45.0,
            float(comp_seco_ideal),
            0.1,
        )


    st.divider()


    if st.button(
        "GERAR DIAGNOSTICO DO LOTE",
        type="primary",
        use_container_width=True,
    ):

        st.session_state.diagnostico_gerado = True


    if st.session_state.diagnostico_gerado:


        (
            pred_res,
            pred_res_ml,
            media_local,
            confianca_res,
            vizinhos,
        ) = prever_residuo_inteligente(
            m_res,
            df_treino_ia,
            pct_amarelo,
            pct_branco,
            umidade,
        )


        X_pes = pd.DataFrame(
            [
                {
                    "esp_parede": esp_parede,
                    "largura_cm": largura_cm,
                    "comprimento_cm": comprimento_cm,
                    "umidade": umidade,
                }
            ]
        )


        if m_pes is not None:

            pred_pes = float(
                m_pes.predict(X_pes)[0]
            )

        else:

            pred_pes = peso_padrao


        X_ret = pd.DataFrame(
            [
                {
                    "pct_preto_ia": pct_preto,
                    "pct_amarelo_ia": pct_amarelo,
                    "pct_branco_ia": pct_branco,
                    "umidade": umidade,
                    "esp_parede": esp_parede,
                }
            ]
        )


        if m_ret is not None:

            pred_ret = float(
                m_ret.predict(X_ret)[0]
            )

        else:

            pred_ret = 3.0


        st.header(
            "Resultados Previstos pela IA"
        )


        diff_comp = (
            comprimento_cm
            - comp_seco_ideal
        )


        if diff_comp > 0.15:

            st.warning(
                f"ALERTA DE CORTE: bloco com "
                f"{comprimento_cm:.1f} cm, "
                f"{diff_comp*10:.0f} mm acima do ideal."
            )


        elif diff_comp < -0.15:

            st.warning(
                f"ATENCAO: bloco com "
                f"{comprimento_cm:.1f} cm, "
                f"{abs(diff_comp)*10:.0f} mm abaixo do ideal."
            )


        res1, res2, res3 = st.columns(3)


        with res1:

            st.metric(
                "Residuo Previsto",
                f"{pred_res:.1f}%",
            )


            if pred_res > 32:

                class_res = (
                    "BLOCO FRACO / ARENOSO"
                )

                st.error(class_res)

                st.caption(
                    "Tendencia acima da faixa ideal. "
                    "Considere reduzir Branco ou aumentar Preto."
                )


            elif pred_res < 28:

                class_res = (
                    "BLOCO FORTE / ARGILOSO"
                )

                st.warning(class_res)

                st.caption(
                    "Tendencia abaixo da faixa ideal."
                )


            else:

                class_res = (
                    "FAIXA IDEAL"
                )

                st.success(
                    "FAIXA IDEAL (28% a 32%)"
                )


            st.caption(
                f"Confianca da previsao: {confianca_res}"
            )


        with res2:

            st.metric(
                "Retracao Prevista",
                f"{pred_ret:.1f}%",
            )

            comp_estimado_queimado = (
                comprimento_cm
                * (1 - pred_ret / 100)
            )

            st.caption(
                f"Comprimento Estimado: "
                f"{comp_estimado_queimado:.1f} cm"
            )


        excesso_g = (
            pred_pes
            - peso_padrao
        ) * 1000


        with res3:

            st.metric(
                "Peso Previsto",
                f"{pred_pes:.3f} kg",
                delta=f"{excesso_g:+.0f}g vs Padrao",
                delta_color="inverse",
            )


            if excesso_g > 50:

                st.error(
                    "ACIMA DO PADRAO"
                )

            elif excesso_g < -50:

                st.warning(
                    "ABAIXO DO PADRAO"
                )

            else:

                st.success(
                    "DENTRO DO PADRAO"
                )


        # ====================================================
        # EXPLICACAO DA PREVISAO
        # ====================================================

        with st.expander(
            "Como a IA chegou nesta previsao?"
        ):

            st.write(
                f"Previsao geral do modelo: "
                f"{pred_res_ml:.2f}%"
            )

            if media_local is not None:

                st.write(
                    f"Media ponderada dos lotes mais semelhantes: "
                    f"{media_local:.2f}%"
                )

            st.write(
                f"Previsao final: {pred_res:.2f}%"
            )

            st.write(
                f"Nivel de confianca: {confianca_res}"
            )

            if len(vizinhos) > 0:

                st.subheader(
                    "Lotes mais semelhantes encontrados"
                )

                cols_show = [
                    "data",
                    "modo",
                    "pct_preto_ia",
                    "pct_amarelo_ia",
                    "pct_branco_ia",
                    "umidade",
                    "residuo",
                ]

                viz_show = vizinhos[
                    cols_show
                ].copy()

                viz_show.columns = [
                    "Data",
                    "Modo",
                    "% Preto",
                    "% Amarelo",
                    "% Branco",
                    "Umidade",
                    "Residuo Real",
                ]

                viz_show["% Preto"] *= 100
                viz_show["% Amarelo"] *= 100
                viz_show["% Branco"] *= 100

                st.dataframe(
                    viz_show,
                    use_container_width=True,
                )


        texto_fin_wa = ""


        if excesso_g > 0:

            st.divider()

            st.subheader(
                "Impacto Financeiro (Excesso de Massa)"
            )

            c_p1, c_p2 = st.columns(2)


            with c_p1:

                prod_dia = st.number_input(
                    "Producao Planejada do Dia (blocos):",
                    1000,
                    200000,
                    50000,
                    5000,
                )


            with c_p2:

                custo_barro = st.number_input(
                    "Custo da Tonelada do Barro (R$/ton):",
                    10.0,
                    200.0,
                    50.0,
                    5.0,
                )


            ton_perdidas_dia = (
                excesso_g
                / 1000
                * prod_dia
                / 1000
            )

            prejuizo_dia = (
                ton_perdidas_dia
                * custo_barro
            )

            prejuizo_mes = (
                prejuizo_dia
                * 25
            )


            st.error(
                f"Desperdicio estimado: "
                f"{ton_perdidas_dia:.2f} toneladas/dia\n\n"
                f"Prejuizo diario: R$ {prejuizo_dia:,.2f}\n\n"
                f"Impacto mensal: R$ {prejuizo_mes:,.2f}"
            )


            texto_fin_wa = (
                f"\nPerda: {ton_perdidas_dia:.2f} ton/dia"
            )


        st.divider()


        msg_wa_diag = (
            f"CeramicaIA - Diagnostico\n\n"
            f"Produto: {codigo_prod}\n"
            f"Mistura: {mistura_desc}\n"
            f"Preto: {pct_preto*100:.1f}%\n"
            f"Amarelo: {pct_amarelo*100:.1f}%\n"
            f"Branco: {pct_branco*100:.1f}%\n"
            f"Umidade: {umidade:.1f}%\n"
            f"Parede: {esp_parede:.2f} cm\n"
            f"Corte: {comprimento_cm:.1f} cm\n\n"
            f"Residuo previsto: {pred_res:.1f}%\n"
            f"Confianca: {confianca_res}\n"
            f"Retracao: {pred_ret:.1f}%\n"
            f"Peso: {pred_pes:.3f} kg"
            f"{texto_fin_wa}\n\n"
            f"Gerado pelo CeramicaIA"
        )


        wa_url_diag = (
            "https://wa.me/?text="
            + urllib.parse.quote(
                msg_wa_diag
            )
        )


        st.link_button(
            "Compartilhar Diagnostico no WhatsApp",
            wa_url_diag,
            use_container_width=True,
        )


# ============================================================
# ABA 2 - REGISTRAR ANALISE
# ============================================================

with tab_reg:

    st.header(
        "Registrar Analise de Laboratorio"
    )

    st.caption(
        "Cada novo resultado passa a fazer parte do aprendizado "
        "da IA de residuo."
    )


    df_barros_reg = (
        st.session_state.catalogo_barros[
            st.session_state.catalogo_barros["status"]
            == "Ativo"
        ]
    )


    pretos_reg = (
        df_barros_reg[
            df_barros_reg["tipo_base"] == "Preto"
        ]["codigo"].tolist()
    )

    amarelos_reg = (
        ["Nenhum"]
        + df_barros_reg[
            df_barros_reg["tipo_base"]
            == "Amarelo"
        ]["codigo"].tolist()
    )

    brancos_reg = (
        ["Nenhum"]
        + df_barros_reg[
            df_barros_reg["tipo_base"]
            == "Branco"
        ]["codigo"].tolist()
    )


    produtos_reg = (
        st.session_state.catalogo_produtos[
            st.session_state.catalogo_produtos["status"]
            == "Ativo"
        ]
    )


    with st.form(
        "form_registro_lote",
        clear_on_submit=True,
    ):

        st.subheader(
            "1. Identificacao"
        )

        c1, c2, c3 = st.columns(3)


        with c1:

            data_lote = st.date_input(
                "Data do Teste",
                datetime.now(),
            )

            prod_lote = st.selectbox(
                "Produto Testado",
                produtos_reg[
                    "chave_comercial"
                ].tolist(),
            )


        produto_row = produtos_reg[
            produtos_reg["chave_comercial"]
            == prod_lote
        ].iloc[0]

        codigo_selecionado = (
            produto_row["codigo"]
        )

        comp_sugerido = float(
            produto_row["comp_seco_ideal"]
        )

        peso_meta = float(
            produto_row["peso_padrao"]
        )


        with c2:

            cod_p_reg = st.selectbox(
                "Codigo Barro Preto:",
                pretos_reg,
            )

            cod_a_reg = st.selectbox(
                "Codigo Barro Amarelo:",
                amarelos_reg,
            )

            cod_b_reg = st.selectbox(
                "Codigo Barro Branco:",
                brancos_reg,
            )


        with c3:

            modo_lote = st.selectbox(
                "Tipo de Producao",
                [
                    "Unica",
                    "Mesclada",
                ],
            )


        st.subheader(
            "2. Quantidade de Conchas"
        )


        ca, cb = st.columns(2)


        with ca:

            st.caption(
                "Receita A"
            )

            p_a = st.number_input(
                "Preto A",
                0,
                10,
                4,
            )

            a_a = st.number_input(
                "Amarelo A",
                0,
                10,
                0,
            )

            b_a = st.number_input(
                "Branco A",
                0,
                10,
                1,
            )


        with cb:

            st.caption(
                "Receita B (somente Mesclada)"
            )

            p_b = st.number_input(
                "Preto B",
                0,
                10,
                4,
            )

            a_b = st.number_input(
                "Amarelo B",
                0,
                10,
                0,
            )

            b_b = st.number_input(
                "Branco B",
                0,
                10,
                1,
            )


        st.subheader(
            "3. Medicoes Reais"
        )


        c4, c5, c6, c7 = st.columns(4)


        with c4:

            umidade_real = st.number_input(
                "Umidade Real (%)",
                0.0,
                40.0,
                16.0,
                0.1,
            )


        with c5:

            residuo_real = st.number_input(
                "Residuo Real (%)",
                0.0,
                60.0,
                30.0,
                0.1,
            )


        with c6:

            retracao_real = st.number_input(
                "Retracao Real (%)",
                0.0,
                10.0,
                3.0,
                0.1,
            )


        with c7:

            esp_real = st.number_input(
                "Espessura Parede (cm)",
                0.0,
                2.0,
                0.65,
                0.01,
            )


        c8, c9, c10 = st.columns(3)


        with c8:

            comp_real = st.number_input(
                "Comprimento Verde (cm)",
                10.0,
                50.0,
                comp_sugerido,
                0.1,
            )


        with c9:

            peso_real = st.number_input(
                "Peso Real (kg)",
                0.0,
                15.0,
                2.800,
                0.001,
            )


        with c10:

            obs = st.text_area(
                "Observacoes:",
                "Teste de rotina",
            )


        salvar_lote = st.form_submit_button(
            "Salvar Registro e Recalibrar IA",
            type="primary",
            use_container_width=True,
        )


    if salvar_lote:


        if modo_lote == "Unica":

            p_b_salvar = p_a
            a_b_salvar = a_a
            b_b_salvar = b_a

        else:

            p_b_salvar = p_b
            a_b_salvar = a_b
            b_b_salvar = b_b


        (
            pct_p,
            pct_a,
            pct_b,
        ) = calcular_percentuais_receita(
            modo_lote,
            p_a,
            a_a,
            b_a,
            p_b_salvar,
            a_b_salvar,
            b_b_salvar,
        )


        # Previsao ANTES de ensinar o novo resultado

        (
            previsao_antes,
            _,
            _,
            confianca_antes,
            _,
        ) = prever_residuo_inteligente(
            m_res,
            df_treino_ia,
            pct_a,
            pct_b,
            umidade_real,
        )


        class_res = (
            "fraco"
            if residuo_real > 32
            else (
                "forte"
                if residuo_real < 28
                else "ideal"
            )
        )


        excesso = (
            peso_real - peso_meta
        ) * 1000


        novo_row = {
            "data": data_lote.strftime(
                "%Y-%m-%d"
            ),
            "modo": modo_lote,
            "cod_barro_preto": cod_p_reg,
            "cod_barro_amarelo": cod_a_reg,
            "cod_barro_branco": cod_b_reg,
            "preto_a": p_a,
            "amarelo_a": a_a,
            "branco_a": b_a,
            "preto_b": p_b_salvar,
            "amarelo_b": a_b_salvar,
            "branco_b": b_b_salvar,
            "pct_preto": round(
                pct_p,
                4,
            ),
            "pct_amarelo": round(
                pct_a,
                4,
            ),
            "pct_branco": round(
                pct_b,
                4,
            ),
            "umidade": umidade_real,
            "residuo": residuo_real,
            "retracao": retracao_real,
            "esp_parede": esp_real,
            "peso": peso_real,
            "comprimento": comp_real,
            "tipo_bloco": codigo_selecionado,
            "class_residuo": class_res,
            "excesso_peso": round(
                excesso,
                0,
            ),
            "observacoes": obs,
        }


        st.session_state.df_master = pd.concat(
            [
                pd.DataFrame(
                    [novo_row]
                ),
                st.session_state.df_master,
            ],
            ignore_index=True,
        )


        persistir_dados(
            "lotes"
        )


        erro = abs(
            residuo_real
            - previsao_antes
        )


        st.success(
            "Lote salvo. O resultado real entrou no banco "
            "e sera usado no proximo treinamento da IA."
        )


        st.subheader(
            "Previsao x Resultado Real"
        )


        cc1, cc2, cc3 = st.columns(3)


        with cc1:

            st.metric(
                "Previsao antes da analise",
                f"{previsao_antes:.1f}%",
            )


        with cc2:

            st.metric(
                "Resultado Real",
                f"{residuo_real:.1f}%",
            )


        with cc3:

            st.metric(
                "Erro",
                f"{erro:.1f} ponto(s) %",
            )


        st.caption(
            f"Confianca que a IA tinha antes de conhecer "
            f"este resultado: {confianca_antes}"
        )


    st.divider()


    st.subheader(
        f"Base de Dados Completa "
        f"({len(st.session_state.df_master)} lotes)"
    )


    st.dataframe(
        st.session_state.df_master,
        use_container_width=True,
    )


    csv_completo = (
        st.session_state.df_master
        .to_csv(index=False)
        .encode("utf-8")
    )


    st.download_button(
        "BAIXAR PLANILHA COMPLETA (BACKUP CSV)",
        csv_completo,
        file_name=(
            "ceramica_lotes_"
            + datetime.now().strftime(
                "%Y%m%d"
            )
            + ".csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================
# ABA 3 - BARRO PURO
# SOMENTE HISTORICO / PESQUISA
# NAO INTERFERE NA IA
# ============================================================

with tab_puro:

    st.header(
        "Analise de Barro Puro"
    )

    st.info(
        "Estas analises sao armazenadas para estudo da materia-prima. "
        "Neste momento elas NAO alteram a previsao de residuo da IA."
    )


    barros_puro = (
        st.session_state.catalogo_barros[
            st.session_state.catalogo_barros["status"]
            == "Ativo"
        ]
    )


    lista_barros_puro = (
        barros_puro["codigo"].tolist()
    )


    p1, p2 = st.columns(
        [1, 2]
    )


    with p1:

        with st.form(
            "form_barro_puro",
            clear_on_submit=True,
        ):

            data_puro = st.date_input(
                "Data da Amostra",
                datetime.now(),
            )

            cod_puro = st.selectbox(
                "Barro:",
                lista_barros_puro,
            )

            peso_amostra = st.number_input(
                "Peso da Amostra Seca (g)",
                1.0,
                5000.0,
                100.0,
                1.0,
            )

            peso_residuo = st.number_input(
                "Peso do Residuo Seco (g)",
                0.0,
                5000.0,
                30.0,
                1.0,
            )


            pct_puro = (
                peso_residuo
                / peso_amostra
                * 100
            )


            st.info(
                f"Residuo Puro: {pct_puro:.2f}%"
            )


            obs_puro = st.text_area(
                "Observacoes:",
                "Amostra de recebimento",
            )


            salvar_puro = st.form_submit_button(
                "Salvar Analise de Barro Puro",
                type="primary",
                use_container_width=True,
            )


        if salvar_puro:

            novo = {
                "data": data_puro.strftime(
                    "%Y-%m-%d"
                ),
                "codigo_barro": cod_puro,
                "peso_amostra_g": peso_amostra,
                "peso_residuo_g": peso_residuo,
                "pct_residuo_puro": round(
                    pct_puro,
                    2,
                ),
                "observacoes": obs_puro,
            }


            st.session_state.analises_puro = pd.concat(
                [
                    pd.DataFrame([novo]),
                    st.session_state.analises_puro,
                ],
                ignore_index=True,
            )


            persistir_dados(
                "puro"
            )


            st.success(
                "Analise de barro puro salva."
            )


    with p2:

        st.subheader(
            "Historico dos Barros Puros"
        )


        if len(
            st.session_state.analises_puro
        ):

            st.dataframe(
                st.session_state.analises_puro,
                use_container_width=True,
            )

        else:

            st.info(
                "Ainda nao existem analises de barro puro."
            )


# ============================================================
# ABA 4 - BARROS
# ============================================================

with tab_barros:

    st.header(
        "Cadastro e Controle de Barros / Jazidas"
    )


    c1, c2 = st.columns(2)


    with c1:

        st.subheader(
            "Cadastrar Novo Barro"
        )


        with st.form(
            "novo_barro",
            clear_on_submit=True,
        ):

            novo_cod = st.text_input(
                "Codigo Oficial:"
            )

            novo_nome = st.text_input(
                "Nome / Apelido:"
            )

            novo_tipo = st.selectbox(
                "Tipo:",
                [
                    "Preto",
                    "Amarelo",
                    "Branco",
                ],
            )

            nova_loc = st.text_input(
                "Localidade:"
            )

            novo_res_puro = st.number_input(
                "Residuo Puro de Referencia (%)",
                0.0,
                100.0,
                0.0,
                0.1,
                help=(
                    "Somente cadastro e acompanhamento. "
                    "Nao influencia a IA de residuo."
                ),
            )

            cadastrar = st.form_submit_button(
                "Cadastrar Barro",
                type="primary",
                use_container_width=True,
            )


        if cadastrar:

            cod = novo_cod.strip().upper()


            if not cod or not novo_nome.strip():

                st.error(
                    "Informe codigo e nome."
                )


            elif cod in st.session_state.catalogo_barros["codigo"].values:

                st.error(
                    "Codigo ja cadastrado."
                )


            else:

                novo = {
                    "codigo": cod,
                    "nome": novo_nome.strip(),
                    "tipo_base": novo_tipo,
                    "localidade": nova_loc.strip(),
                    "residuo_puro": novo_res_puro,
                    "status": "Ativo",
                }


                st.session_state.catalogo_barros = pd.concat(
                    [
                        st.session_state.catalogo_barros,
                        pd.DataFrame([novo]),
                    ],
                    ignore_index=True,
                )


                persistir_dados(
                    "barros"
                )

                st.success(
                    "Barro cadastrado."
                )

                st.rerun()


    with c2:

        st.subheader(
            "Editar Barro"
        )


        codigos = (
            st.session_state.catalogo_barros[
                "codigo"
            ].tolist()
        )


        if codigos:

            sel = st.selectbox(
                "Selecione:",
                codigos,
            )

            atual = (
                st.session_state.catalogo_barros[
                    st.session_state.catalogo_barros["codigo"]
                    == sel
                ].iloc[0]
            )


            with st.form(
                "editar_barro"
            ):

                edit_cod = st.text_input(
                    "Codigo:",
                    value=str(
                        atual["codigo"]
                    ),
                )

                edit_nome = st.text_input(
                    "Nome:",
                    value=str(
                        atual["nome"]
                    ),
                )

                tipos = [
                    "Preto",
                    "Amarelo",
                    "Branco",
                ]

                tipo_atual = str(
                    atual["tipo_base"]
                )

                edit_tipo = st.selectbox(
                    "Tipo:",
                    tipos,
                    index=(
                        tipos.index(tipo_atual)
                        if tipo_atual in tipos
                        else 0
                    ),
                )

                edit_loc = st.text_input(
                    "Localidade:",
                    value=str(
                        atual["localidade"]
                    ),
                )


                try:

                    rp_atual = float(
                        atual["residuo_puro"]
                    )

                except Exception:

                    rp_atual = 0.0


                edit_rp = st.number_input(
                    "Residuo Puro (%)",
                    0.0,
                    100.0,
                    rp_atual,
                    0.1,
                )


                status_lista = [
                    "Ativo",
                    "Inativo",
                ]

                status_atual = str(
                    atual["status"]
                )

                edit_status = st.selectbox(
                    "Status:",
                    status_lista,
                    index=(
                        status_lista.index(status_atual)
                        if status_atual in status_lista
                        else 0
                    ),
                )


                salvar_edit = st.form_submit_button(
                    "Salvar Alteracoes",
                    type="primary",
                    use_container_width=True,
                )


            if salvar_edit:

                idx = (
                    st.session_state.catalogo_barros[
                        st.session_state.catalogo_barros["codigo"]
                        == sel
                    ].index[0]
                )


                novo_codigo = (
                    edit_cod.strip().upper()
                )


                if (
                    novo_codigo != sel
                    and novo_codigo
                    in st.session_state.catalogo_barros["codigo"].values
                ):

                    st.error(
                        "Codigo ja existe."
                    )


                else:

                    if novo_codigo != sel:

                        for col in [
                            "cod_barro_preto",
                            "cod_barro_amarelo",
                            "cod_barro_branco",
                        ]:

                            if col in st.session_state.df_master.columns:

                                st.session_state.df_master[col] = (
                                    st.session_state.df_master[col]
                                    .replace(
                                        sel,
                                        novo_codigo,
                                    )
                                )


                        if len(
                            st.session_state.analises_puro
                        ) > 0:

                            st.session_state.analises_puro[
                                "codigo_barro"
                            ] = (
                                st.session_state.analises_puro[
                                    "codigo_barro"
                                ].replace(
                                    sel,
                                    novo_codigo,
                                )
                            )


                    st.session_state.catalogo_barros.at[
                        idx,
                        "codigo"
                    ] = novo_codigo

                    st.session_state.catalogo_barros.at[
                        idx,
                        "nome"
                    ] = edit_nome.strip()

                    st.session_state.catalogo_barros.at[
                        idx,
                        "tipo_base"
                    ] = edit_tipo

                    st.session_state.catalogo_barros.at[
                        idx,
                        "localidade"
                    ] = edit_loc.strip()

                    st.session_state.catalogo_barros.at[
                        idx,
                        "residuo_puro"
                    ] = edit_rp

                    st.session_state.catalogo_barros.at[
                        idx,
                        "status"
                    ] = edit_status


                    persistir_dados(
                        "barros"
                    )

                    persistir_dados(
                        "lotes"
                    )

                    persistir_dados(
                        "puro"
                    )


                    st.success(
                        "Barro atualizado."
                    )

                    st.rerun()


    st.divider()

    st.dataframe(
        st.session_state.catalogo_barros,
        use_container_width=True,
    )


# ============================================================
# ABA 5 - PRODUTOS
# ============================================================

with tab_produtos:

    st.header(
        "Cadastro e Controle de Produtos / Blocos"
    )


    cp1, cp2 = st.columns(2)


    with cp1:

        st.subheader(
            "Cadastrar Novo Produto"
        )


        with st.form(
            "novo_produto",
            clear_on_submit=True,
        ):

            n_cod = st.text_input(
                "Codigo do Produto:"
            )

            n_nome = st.text_input(
                "Descricao:"
            )

            n_larg = st.number_input(
                "Largura (cm)",
                5.0,
                30.0,
                9.0,
                0.5,
            )

            n_nom = st.number_input(
                "Comprimento Nominal (cm)",
                5.0,
                50.0,
                19.0,
                0.5,
            )

            n_verde = st.number_input(
                "Comprimento Verde Ideal (cm)",
                5.0,
                55.0,
                20.0,
                0.5,
            )

            n_peso = st.number_input(
                "Peso Padrao (kg)",
                0.5,
                15.0,
                2.8,
                0.05,
                format="%.3f",
            )


            cad_prod = st.form_submit_button(
                "Cadastrar Produto",
                type="primary",
                use_container_width=True,
            )


        if cad_prod:

            cod = n_cod.strip().upper()


            if not cod or not n_nome.strip():

                st.error(
                    "Informe codigo e descricao."
                )


            elif cod in st.session_state.catalogo_produtos["codigo"].values:

                st.error(
                    "Produto ja existe."
                )


            else:

                chave = (
                    f"{cod} "
                    f"({n_larg:.0f}x{n_nom:.0f}x{n_nom:.0f} cm) "
                    f"- {n_nome.strip()}"
                )


                novo = {
                    "chave_comercial": chave,
                    "codigo": cod,
                    "largura": n_larg,
                    "comprimento_nominal": n_nom,
                    "comp_seco_ideal": n_verde,
                    "peso_padrao": n_peso,
                    "status": "Ativo",
                }


                st.session_state.catalogo_produtos = pd.concat(
                    [
                        st.session_state.catalogo_produtos,
                        pd.DataFrame([novo]),
                    ],
                    ignore_index=True,
                )


                persistir_dados(
                    "produtos"
                )

                st.success(
                    "Produto cadastrado."
                )

                st.rerun()


    with cp2:

        st.subheader(
            "Editar Produto"
        )


        cod_produtos = (
            st.session_state.catalogo_produtos[
                "codigo"
            ].tolist()
        )


        if cod_produtos:

            prod_sel = st.selectbox(
                "Produto:",
                cod_produtos,
            )


            atual = (
                st.session_state.catalogo_produtos[
                    st.session_state.catalogo_produtos["codigo"]
                    == prod_sel
                ].iloc[0]
            )


            with st.form(
                "editar_produto"
            ):

                ep_cod = st.text_input(
                    "Codigo:",
                    value=str(
                        atual["codigo"]
                    ),
                )


                descricao = str(
                    atual["chave_comercial"]
                ).split(" - ")[-1]


                ep_nome = st.text_input(
                    "Descricao:",
                    value=descricao,
                )

                ep_larg = st.number_input(
                    "Largura (cm)",
                    5.0,
                    30.0,
                    float(atual["largura"]),
                    0.5,
                )

                ep_nom = st.number_input(
                    "Comprimento Nominal (cm)",
                    5.0,
                    50.0,
                    float(
                        atual["comprimento_nominal"]
                    ),
                    0.5,
                )

                ep_verde = st.number_input(
                    "Comprimento Verde Ideal (cm)",
                    5.0,
                    55.0,
                    float(
                        atual["comp_seco_ideal"]
                    ),
                    0.5,
                )

                ep_peso = st.number_input(
                    "Peso Padrao (kg)",
                    0.5,
                    15.0,
                    float(
                        atual["peso_padrao"]
                    ),
                    0.05,
                    format="%.3f",
                )


                statuses = [
                    "Ativo",
                    "Inativo",
                ]

                atual_status = str(
                    atual["status"]
                )

                ep_status = st.selectbox(
                    "Status:",
                    statuses,
                    index=(
                        statuses.index(atual_status)
                        if atual_status in statuses
                        else 0
                    ),
                )


                salvar_prod = st.form_submit_button(
                    "Salvar Alteracoes",
                    type="primary",
                    use_container_width=True,
                )


            if salvar_prod:

                novo_cod = (
                    ep_cod.strip().upper()
                )


                idx = (
                    st.session_state.catalogo_produtos[
                        st.session_state.catalogo_produtos["codigo"]
                        == prod_sel
                    ].index[0]
                )


                if (
                    novo_cod != prod_sel
                    and novo_cod
                    in st.session_state.catalogo_produtos["codigo"].values
                ):

                    st.error(
                        "Codigo ja existe."
                    )


                else:

                    if novo_cod != prod_sel:

                        st.session_state.df_master[
                            "tipo_bloco"
                        ] = (
                            st.session_state.df_master[
                                "tipo_bloco"
                            ].replace(
                                prod_sel,
                                novo_cod,
                            )
                        )


                    nova_chave = (
                        f"{novo_cod} "
                        f"({ep_larg:.0f}x{ep_nom:.0f}x{ep_nom:.0f} cm) "
                        f"- {ep_nome.strip()}"
                    )


                    st.session_state.catalogo_produtos.at[
                        idx,
                        "codigo"
                    ] = novo_cod

                    st.session_state.catalogo_produtos.at[
                        idx,
                        "chave_comercial"
                    ] = nova_chave

                    st.session_state.catalogo_produtos.at[
                        idx,
                        "largura"
                    ] = ep_larg

                    st.session_state.catalogo_produtos.at[
                        idx,
                        "comprimento_nominal"
                    ] = ep_nom

                    st.session_state.catalogo_produtos.at[
                        idx,
                        "comp_seco_ideal"
                    ] = ep_verde

                    st.session_state.catalogo_produtos.at[
                        idx,
                        "peso_padrao"
                    ] = ep_peso

                    st.session_state.catalogo_produtos.at[
                        idx,
                        "status"
                    ] = ep_status


                    persistir_dados(
                        "produtos"
                    )

                    persistir_dados(
                        "lotes"
                    )


                    st.success(
                        "Produto atualizado."
                    )

                    st.rerun()


    st.divider()

    st.dataframe(
        st.session_state.catalogo_produtos,
        use_container_width=True,
    )
