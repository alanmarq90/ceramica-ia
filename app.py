# ============================================================
# CERAMICAIA v16.2
# GESTAO DE MISTURAS, ANALISES E RASTREABILIDADE
# Peso: modelo fisico proporcional calibrado por produto
# ============================================================

import os
import urllib.parse
from datetime import date, datetime

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
# CONSTANTES
# ============================================================

APP_VERSION = "16.2"
VERSAO_MODELOS = "16.2-peso-fisico-calibrado"
DIAS_PRODUCAO_MES = 26

# Referencia da fabrica para o peso padrao dos produtos
PAREDE_PADRAO_CM = 0.65

# Calibracao do peso
MIN_REGISTROS_CALIBRACAO = 5
RAZAO_MIN_VALIDA = 0.60
RAZAO_MAX_VALIDA = 1.60
FATOR_MIN = 0.80
FATOR_MAX = 1.20


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
    .main-header { font-size: 28px; font-weight: 700; color: #b23b00; margin-bottom: 0; }
    .sub-header { font-size: 14px; color: #666666; margin-top: 4px; }
    .status-ok { background-color: #d4edda; color: #155724; padding: 9px 12px; border-radius: 7px; font-size: 13px; margin-bottom: 8px; }
    .status-local { background-color: #fff3cd; color: #856404; padding: 9px 12px; border-radius: 7px; font-size: 13px; margin-bottom: 8px; }
    .status-erro { background-color: #f8d7da; color: #721c24; padding: 9px 12px; border-radius: 7px; font-size: 13px; margin-bottom: 8px; }
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
    '<div class="sub-header">Previsao baseada nos lotes reais, controle dimensional, gestao de barros e calculo de perdas</div>',
    unsafe_allow_html=True,
)
st.caption(f"Versao {APP_VERSION}")
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
    except Exception as erro_conexao:
        st.sidebar.markdown(
            '<div class="status-local">Banco de dados: CSV Local<br>'
            f"Aviso: {str(erro_conexao)[:100]}</div>",
            unsafe_allow_html=True,
        )
else:
    st.sidebar.markdown(
        '<div class="status-local">Banco de dados: CSV Local<br>Motivo: gspread nao instalado</div>',
        unsafe_allow_html=True,
    )

if MODO_SHEETS:
    st.sidebar.markdown(
        '<div class="status-ok">Banco de dados: Google Sheets conectado</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# ESTRUTURA DAS TABELAS
# ============================================================

COLUNAS_BARROS = ["codigo", "nome", "tipo_base", "localidade", "residuo_puro", "status"]

COLUNAS_PRODUTOS = [
    "chave_comercial", "codigo", "largura", "comprimento_nominal",
    "comp_seco_ideal", "peso_padrao", "status",
]

COLUNAS_LOTES = [
    "data", "modo", "cod_barro_preto", "cod_barro_amarelo", "cod_barro_branco",
    "preto_a", "amarelo_a", "branco_a", "preto_b", "amarelo_b", "branco_b",
    "pct_preto", "pct_amarelo", "pct_branco", "umidade", "residuo", "retracao",
    "esp_parede", "peso", "comprimento", "tipo_bloco", "class_residuo",
    "excesso_peso", "observacoes",
]

COLUNAS_PURO = [
    "data", "codigo_barro", "peso_amostra_g", "peso_residuo_g",
    "pct_residuo_puro", "observacoes",
]


# ============================================================
# DADOS INICIAIS
# ============================================================

BARROS_INICIAIS = [
    {"codigo": "01_BR_ARG_PRETO_SV", "nome": "Barro Argiloso Preto (Sao Vicente)",
     "tipo_base": "Preto", "localidade": "Sao Vicente (SV)", "residuo_puro": 0.0, "status": "Ativo"},
    {"codigo": "02_BR_ARG_AMAREL_STPREZ", "nome": "Barro Amarelo (Sitio Prazeres)",
     "tipo_base": "Amarelo", "localidade": "Sitio Prazeres (STPRAZ)", "residuo_puro": 0.0, "status": "Ativo"},
    {"codigo": "03_BR_AREN_BRANCO_STPRAZ", "nome": "Barro Arenoso Branco (Sitio Prazeres)",
     "tipo_base": "Branco", "localidade": "Sitio Prazeres (STPRAZ)", "residuo_puro": 0.0, "status": "Ativo"},
]

PRODUTOS_INICIAIS = [
    {"chave_comercial": "01-BLP (9x19x19 cm) - Vedacao Padrao", "codigo": "01-BLP", "largura": 9.0,
     "comprimento_nominal": 19.0, "comp_seco_ideal": 20.0, "peso_padrao": 2.800, "status": "Ativo"},
    {"chave_comercial": "BP14 (14x19x19 cm) - Estrutural Curto", "codigo": "BP14", "largura": 14.0,
     "comprimento_nominal": 19.0, "comp_seco_ideal": 20.0, "peso_padrao": 3.800, "status": "Ativo"},
    {"chave_comercial": "02-BLG (9x19x39 cm) - Bloco Grande / Canaleta 9", "codigo": "02-BLG", "largura": 9.0,
     "comprimento_nominal": 39.0, "comp_seco_ideal": 40.0, "peso_padrao": 5.500, "status": "Ativo"},
    {"chave_comercial": "BG14 (14x19x39 cm) - Estrutural Grande 14", "codigo": "BG14", "largura": 14.0,
     "comprimento_nominal": 39.0, "comp_seco_ideal": 40.0, "peso_padrao": 7.000, "status": "Ativo"},
]


# ============================================================
# FUNCOES DE DADOS
# ============================================================

def garantir_colunas(df, colunas):
    if df is None:
        return pd.DataFrame(columns=colunas)
    df = df.copy()
    for coluna in colunas:
        if coluna not in df.columns:
            df[coluna] = np.nan
    return df


def ler_dados_sheets(worksheet, colunas):
    try:
        registros = worksheet.get_all_records()
        if registros:
            return garantir_colunas(pd.DataFrame(registros), colunas)
        return pd.DataFrame(columns=colunas)
    except Exception as erro:
        st.error(f"Nao foi possivel ler uma das tabelas do Google Sheets. Detalhes: {erro}")
        return None


def salvar_no_sheets(worksheet, df):
    try:
        worksheet.clear()
        df_str = df.fillna("").astype(str)
        dados_lista = [df_str.columns.tolist()] + df_str.values.tolist()
        worksheet.update(values=dados_lista, range_name="A1")
        return True
    except Exception as erro:
        st.error(f"Erro ao sincronizar com Google Sheets: {erro}")
        return False


def carregar_tabela(chave_sessao, worksheet, colunas, arquivo_csv, registros_iniciais=None):
    if chave_sessao in st.session_state:
        return

    df = None

    if MODO_SHEETS:
        df = ler_dados_sheets(worksheet, colunas)
        if df is not None and len(df) == 0 and registros_iniciais is not None:
            df = pd.DataFrame(registros_iniciais)
            salvar_no_sheets(worksheet, df)

    if df is None and os.path.exists(arquivo_csv):
        try:
            df = pd.read_csv(arquivo_csv)
        except Exception:
            df = None

    if df is None:
        if registros_iniciais is not None:
            df = pd.DataFrame(registros_iniciais)
        else:
            df = pd.DataFrame(columns=colunas)

    st.session_state[chave_sessao] = garantir_colunas(df, colunas)


carregar_tabela("catalogo_barros", worksheet_barros, COLUNAS_BARROS,
                "db_catalogo_barros.csv", BARROS_INICIAIS)
carregar_tabela("catalogo_produtos", worksheet_produtos, COLUNAS_PRODUTOS,
                "db_catalogo_produtos.csv", PRODUTOS_INICIAIS)
carregar_tabela("df_master", worksheet_lotes, COLUNAS_LOTES, "db_df_master.csv")
carregar_tabela("analises_puro", worksheet_puro, COLUNAS_PURO, "db_analises_puro.csv")

if "diagnostico_gerado" not in st.session_state:
    st.session_state.diagnostico_gerado = False

if "versao_dados" not in st.session_state:
    st.session_state.versao_dados = 0


def marcar_dados_alterados():
    st.session_state.versao_dados += 1


def persistir_dados(tipo):
    mapa_dados = {
        "barros": (st.session_state.catalogo_barros, worksheet_barros, "db_catalogo_barros.csv"),
        "produtos": (st.session_state.catalogo_produtos, worksheet_produtos, "db_catalogo_produtos.csv"),
        "lotes": (st.session_state.df_master, worksheet_lotes, "db_df_master.csv"),
        "puro": (st.session_state.analises_puro, worksheet_puro, "db_analises_puro.csv"),
    }

    if tipo not in mapa_dados:
        st.error("Tipo de dado invalido para persistencia.")
        return False

    df, worksheet, arquivo_csv = mapa_dados[tipo]

    salvou_sheets = True
    if MODO_SHEETS:
        salvou_sheets = salvar_no_sheets(worksheet, df)

    try:
        df.to_csv(arquivo_csv, index=False)
    except Exception:
        pass

    if salvou_sheets:
        marcar_dados_alterados()
        return True

    return False


# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def campos_preenchidos(*valores):
    return all(valor is not None for valor in valores)


def numero_seguro(valor, padrao=0.0):
    try:
        numero = float(valor)
        if not np.isfinite(numero):
            return padrao
        return numero
    except Exception:
        return padrao


def inteiro_seguro(valor, padrao=0):
    return int(round(numero_seguro(valor, padrao)))


def texto_seguro(valor, padrao=""):
    if valor is None:
        return padrao
    try:
        if pd.isna(valor):
            return padrao
    except Exception:
        pass
    texto = str(valor).strip()
    if texto.lower() in ["nan", "none", "<na>"]:
        return padrao
    return texto


def codigo_opcional(valor):
    codigo = texto_seguro(valor)
    return codigo if codigo else "Nenhum"


def concha_efetiva(valor, codigo_barro):
    if codigo_opcional(codigo_barro) == "Nenhum":
        return 0
    return valor


def data_segura(valor):
    data_convertida = pd.to_datetime(valor, errors="coerce")
    if pd.isna(data_convertida):
        return date.today()
    return data_convertida.date()


def formatar_data(valor):
    data_convertida = pd.to_datetime(valor, errors="coerce")
    if pd.isna(data_convertida):
        return texto_seguro(valor, "-")
    return data_convertida.strftime("%d/%m/%Y")


def formatar_numero(valor, casas=1):
    try:
        numero = float(valor)
        if not np.isfinite(numero):
            return "-"
        return f"{numero:.{casas}f}".replace(".", ",")
    except Exception:
        return "-"


def classificar_residuo(residuo):
    residuo = numero_seguro(residuo)
    if residuo > 32:
        return "Fraco / Arenoso"
    if residuo < 28:
        return "Forte / Argiloso"
    return "Faixa ideal"


def classe_residuo_banco(residuo):
    residuo = numero_seguro(residuo)
    if residuo > 32:
        return "fraco"
    if residuo < 28:
        return "forte"
    return "ideal"


def calcular_percentuais_receita(modo, p_a, a_a, b_a, p_b, a_b, b_b):
    p_a, a_a, b_a = numero_seguro(p_a), numero_seguro(a_a), numero_seguro(b_a)
    p_b, a_b, b_b = numero_seguro(p_b), numero_seguro(a_b), numero_seguro(b_b)

    modo_texto = texto_seguro(modo, "Unica").lower()

    if modo_texto.startswith("unica") or modo_texto.startswith("receita unica"):
        total = p_a + a_a + b_a
        if total <= 0:
            return 0.0, 0.0, 0.0
        return p_a / total, a_a / total, b_a / total

    total_preto = p_a + p_b
    total_amarelo = a_a + a_b
    total_branco = b_a + b_b
    total = total_preto + total_amarelo + total_branco

    if total <= 0:
        return 0.0, 0.0, 0.0

    return total_preto / total, total_amarelo / total, total_branco / total


def percentuais_da_linha(row):
    p_a = numero_seguro(row.get("preto_a", 0))
    a_a = numero_seguro(row.get("amarelo_a", 0))
    b_a = numero_seguro(row.get("branco_a", 0))
    p_b = numero_seguro(row.get("preto_b", p_a), p_a)
    a_b = numero_seguro(row.get("amarelo_b", a_a), a_a)
    b_b = numero_seguro(row.get("branco_b", b_a), b_a)
    return calcular_percentuais_receita(row.get("modo", "Unica"), p_a, a_a, b_a, p_b, a_b, b_b)


def rotulo_lote(idx, row):
    return (
        f"{formatar_data(row.get('data'))} | "
        f"{texto_seguro(row.get('tipo_bloco'), 'Sem produto')} | "
        f"Residuo {formatar_numero(row.get('residuo'), 1)}% | "
        f"Registro {idx + 1}"
    )


def rotulo_puro(idx, row):
    return (
        f"{formatar_data(row.get('data'))} | "
        f"{texto_seguro(row.get('codigo_barro'), 'Sem barro')} | "
        f"Residuo {formatar_numero(row.get('pct_residuo_puro'), 2)}% | "
        f"Registro {idx + 1}"
    )


def adicionar_opcao_atual(opcoes, valor_atual):
    opcoes = list(opcoes)
    valor_atual = texto_seguro(valor_atual)
    if valor_atual and valor_atual not in opcoes:
        opcoes.insert(0, valor_atual)
    return opcoes


def mediana_ponderada(valores, pesos):
    valores = np.asarray(valores, dtype=float)
    pesos = np.asarray(pesos, dtype=float)
    if len(valores) == 0:
        return np.nan
    ordem = np.argsort(valores)
    valores_ord = valores[ordem]
    pesos_ord = pesos[ordem]
    acumulado = np.cumsum(pesos_ord)
    corte = acumulado[-1] / 2.0
    posicao = int(np.searchsorted(acumulado, corte))
    posicao = min(posicao, len(valores_ord) - 1)
    return float(valores_ord[posicao])


# ============================================================
# PREPARACAO DA BASE DE TREINAMENTO
# ============================================================

def montar_dataset_treino(df_lotes, df_produtos):
    if df_lotes is None or len(df_lotes) == 0:
        return pd.DataFrame()

    df = garantir_colunas(df_lotes, COLUNAS_LOTES)

    colunas_numericas = [
        "preto_a", "amarelo_a", "branco_a", "preto_b", "amarelo_b", "branco_b",
        "umidade", "residuo", "retracao", "esp_parede", "peso", "comprimento",
    ]
    for coluna in colunas_numericas:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    pct_preto_lista, pct_amarelo_lista, pct_branco_lista = [], [], []

    for _, row in df.iterrows():
        pp, pa, pb = percentuais_da_linha(row)
        pct_preto_lista.append(pp)
        pct_amarelo_lista.append(pa)
        pct_branco_lista.append(pb)

    df["pct_preto_ia"] = pct_preto_lista
    df["pct_amarelo_ia"] = pct_amarelo_lista
    df["pct_branco_ia"] = pct_branco_lista

    df["data_dt"] = pd.to_datetime(df["data"], errors="coerce")
    df["comprimento_cm"] = pd.to_numeric(df["comprimento"], errors="coerce")
    df["tipo_bloco"] = df["tipo_bloco"].apply(lambda v: texto_seguro(v))

    # Referencias do produto para o modelo de peso
    peso_padrao_map = {}
    comp_ideal_map = {}
    try:
        produtos = garantir_colunas(df_produtos, COLUNAS_PRODUTOS)
        for _, prod in produtos.iterrows():
            codigo = texto_seguro(prod.get("codigo"))
            if codigo:
                peso_padrao_map[codigo] = numero_seguro(prod.get("peso_padrao"))
                comp_ideal_map[codigo] = numero_seguro(prod.get("comp_seco_ideal"))
    except Exception:
        pass

    df["peso_padrao_prod"] = df["tipo_bloco"].map(peso_padrao_map)
    df["comp_ideal_prod"] = df["tipo_bloco"].map(comp_ideal_map)

    return df


# ============================================================
# MODELO DE PESO - FISICO PROPORCIONAL CALIBRADO
# ============================================================

def calcular_peso_base(peso_padrao, comp_ideal, esp_parede, comprimento):
    peso_padrao = numero_seguro(peso_padrao)
    comp_ideal = numero_seguro(comp_ideal)
    esp_parede = numero_seguro(esp_parede)
    comprimento = numero_seguro(comprimento)

    if peso_padrao <= 0 or comp_ideal <= 0 or esp_parede <= 0 or comprimento <= 0:
        return np.nan

    return peso_padrao * (esp_parede / PAREDE_PADRAO_CM) * (comprimento / comp_ideal)


def calibrar_modelo_peso(df):
    resultado = {"por_produto": {}, "r2": None, "mae_g": None, "n": 0}

    if df is None or len(df) == 0:
        return resultado

    colunas = ["peso", "esp_parede", "comprimento_cm", "peso_padrao_prod", "comp_ideal_prod", "data_dt"]
    if not all(coluna in df.columns for coluna in colunas):
        return resultado

    base = df.dropna(subset=colunas).copy()
    base = base[
        (base["peso"] > 0)
        & (base["esp_parede"] > 0)
        & (base["comprimento_cm"] > 0)
        & (base["peso_padrao_prod"] > 0)
        & (base["comp_ideal_prod"] > 0)
    ]

    if len(base) == 0:
        return resultado

    base["peso_base"] = (
        base["peso_padrao_prod"]
        * (base["esp_parede"] / PAREDE_PADRAO_CM)
        * (base["comprimento_cm"] / base["comp_ideal_prod"])
    )
    base["razao"] = base["peso"] / base["peso_base"]
    base["peso_temporal"] = calcular_pesos_temporais(base["data_dt"])

    for codigo, grupo in base.groupby("tipo_bloco"):
        codigo = texto_seguro(codigo)
        if not codigo:
            continue

        validos = grupo[
            (grupo["razao"] >= RAZAO_MIN_VALIDA) & (grupo["razao"] <= RAZAO_MAX_VALIDA)
        ]
        n_validos = len(validos)
        n_descartados = len(grupo) - n_validos

        if n_validos >= MIN_REGISTROS_CALIBRACAO:
            fator = mediana_ponderada(validos["razao"].values, validos["peso_temporal"].values)
            fator = float(np.clip(fator, FATOR_MIN, FATOR_MAX))
            origem = "calibrado"
        else:
            fator = 1.0
            origem = "padrao"

        if n_validos > 0:
            erro_g = float(np.mean(np.abs(validos["peso"] - validos["peso_base"] * fator)) * 1000)
        else:
            erro_g = None

        resultado["por_produto"][codigo] = {
            "fator": fator,
            "n_validos": int(n_validos),
            "n_descartados": int(n_descartados),
            "mae_g": erro_g,
            "origem": origem,
        }

    base["fator"] = base["tipo_bloco"].map(
        lambda c: resultado["por_produto"].get(texto_seguro(c), {}).get("fator", 1.0)
    )
    base["previsto"] = base["peso_base"] * base["fator"]

    avaliacao = base[(base["razao"] >= RAZAO_MIN_VALIDA) & (base["razao"] <= RAZAO_MAX_VALIDA)]
    resultado["n"] = int(len(avaliacao))

    if len(avaliacao) >= 2:
        try:
            if avaliacao["peso"].var() > 0:
                resultado["r2"] = round(float(r2_score(avaliacao["peso"], avaliacao["previsto"])), 3)
            resultado["mae_g"] = round(
                float(mean_absolute_error(avaliacao["peso"], avaliacao["previsto"]) * 1000), 1
            )
        except Exception:
            pass

    return resultado


def prever_peso(calibracao, codigo_produto, peso_padrao, comp_ideal, esp_parede, comprimento):
    peso_base = calcular_peso_base(peso_padrao, comp_ideal, esp_parede, comprimento)

    info = None
    if calibracao is not None:
        info = calibracao.get("por_produto", {}).get(texto_seguro(codigo_produto))

    fator = info["fator"] if info else 1.0

    if not np.isfinite(peso_base):
        return numero_seguro(peso_padrao), np.nan, fator, info

    return float(peso_base * fator), float(peso_base), fator, info


# ============================================================
# VARIAVEIS DOS MODELOS DE RESIDUO E RETRACAO
# ============================================================

FEATURES_RESIDUO = ["pct_amarelo_ia", "pct_branco_ia", "umidade"]

FEATURES_RETRACAO = ["pct_preto_ia", "pct_amarelo_ia", "pct_branco_ia", "umidade", "esp_parede"]


def calcular_pesos_temporais(datas):
    datas = pd.to_datetime(datas, errors="coerce")

    if datas.notna().sum() == 0:
        return np.ones(len(datas))

    data_maxima = datas.max()
    idade_dias = (data_maxima - datas).dt.days.fillna(365)
    pesos = np.exp(-idade_dias / 180.0)
    pesos = np.maximum(pesos, 0.10)
    return np.asarray(pesos)


# ============================================================
# TREINAMENTO DOS MODELOS
# ============================================================

def treinar_modelos_ia(df_lotes, df_produtos):
    df = montar_dataset_treino(df_lotes, df_produtos)

    metricas = {
        "n": len(df),
        "n_residuo": 0,
        "r2_peso": None,
        "mae_peso_g": None,
        "n_peso": 0,
        "r2_residuo_treino": None,
        "mae_residuo_validacao": None,
        "r2_retracao": None,
    }

    # --------------------------------------------------------
    # PESO - modelo fisico calibrado (nao usa arvore)
    # --------------------------------------------------------
    calibracao_peso = calibrar_modelo_peso(df)
    metricas["r2_peso"] = calibracao_peso["r2"]
    metricas["mae_peso_g"] = calibracao_peso["mae_g"]
    metricas["n_peso"] = calibracao_peso["n"]

    if len(df) < 5:
        return calibracao_peso, None, None, metricas, df

    # --------------------------------------------------------
    # RESIDUO - logica original mantida
    # --------------------------------------------------------
    df_residuo = df.dropna(subset=FEATURES_RESIDUO + ["residuo", "data_dt"]).copy()
    df_residuo = df_residuo.sort_values("data_dt")
    metricas["n_residuo"] = len(df_residuo)

    modelo_residuo = None

    if len(df_residuo) >= 10:
        X_residuo = df_residuo[FEATURES_RESIDUO].astype(float)
        y_residuo = df_residuo["residuo"].astype(float)
        pesos = calcular_pesos_temporais(df_residuo["data_dt"])

        modelo_residuo = GradientBoostingRegressor(
            random_state=42, n_estimators=100, learning_rate=0.035,
            max_depth=2, min_samples_leaf=4, loss="huber",
        )
        modelo_residuo.fit(X_residuo, y_residuo, sample_weight=pesos)

        try:
            metricas["r2_residuo_treino"] = round(
                float(r2_score(y_residuo, modelo_residuo.predict(X_residuo))), 3
            )
        except Exception:
            pass

        if len(df_residuo) >= 20:
            quantidade_teste = max(5, int(len(df_residuo) * 0.20))
            treino = df_residuo.iloc[:-quantidade_teste].copy()
            teste = df_residuo.iloc[-quantidade_teste:].copy()

            modelo_validacao = GradientBoostingRegressor(
                random_state=42, n_estimators=100, learning_rate=0.035,
                max_depth=2, min_samples_leaf=4, loss="huber",
            )
            modelo_validacao.fit(
                treino[FEATURES_RESIDUO].astype(float),
                treino["residuo"].astype(float),
                sample_weight=calcular_pesos_temporais(treino["data_dt"]),
            )
            pred_test = modelo_validacao.predict(teste[FEATURES_RESIDUO].astype(float))
            metricas["mae_residuo_validacao"] = round(
                float(mean_absolute_error(teste["residuo"].astype(float), pred_test)), 2
            )

    # --------------------------------------------------------
    # RETRACAO
    # --------------------------------------------------------
    df_retracao = df.dropna(subset=FEATURES_RETRACAO + ["retracao"])
    modelo_retracao = None

    if len(df_retracao) >= 5:
        X_retracao = df_retracao[FEATURES_RETRACAO].astype(float)
        y_retracao = df_retracao["retracao"].astype(float)

        modelo_retracao = GradientBoostingRegressor(
            random_state=42, n_estimators=100, learning_rate=0.04, max_depth=2, loss="huber",
        )
        modelo_retracao.fit(X_retracao, y_retracao)

        try:
            metricas["r2_retracao"] = round(
                float(r2_score(y_retracao, modelo_retracao.predict(X_retracao))), 3
            )
        except Exception:
            pass

    return calibracao_peso, modelo_residuo, modelo_retracao, metricas, df


# ============================================================
# TREINAMENTO / RETREINAMENTO
# ============================================================

precisa_treinar = (
    "modelos_ia" not in st.session_state
    or st.session_state.get("versao_treinada") != st.session_state.versao_dados
    or st.session_state.get("versao_codigo_modelos") != VERSAO_MODELOS
)

if precisa_treinar:
    with st.spinner("Calibrando IA com os lotes reais da fabrica..."):
        (calibracao_peso, m_res, m_ret, metricas_ia, df_treino_ia) = treinar_modelos_ia(
            st.session_state.df_master, st.session_state.catalogo_produtos,
        )
        st.session_state.modelos_ia = (calibracao_peso, m_res, m_ret)
        st.session_state.metricas_ia = metricas_ia
        st.session_state.df_treino_ia = df_treino_ia
        st.session_state.versao_treinada = st.session_state.versao_dados
        st.session_state.versao_codigo_modelos = VERSAO_MODELOS
else:
    (calibracao_peso, m_res, m_ret) = st.session_state.modelos_ia
    metricas_ia = st.session_state.metricas_ia
    df_treino_ia = st.session_state.df_treino_ia

IA_RESIDUO_DISPONIVEL = m_res is not None

if IA_RESIDUO_DISPONIVEL:
    st.sidebar.markdown(
        f'<div class="status-ok">IA treinada com {metricas_ia["n_residuo"]} analises de residuo</div>',
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        '<div class="status-erro">IA de residuo sem dados suficientes. '
        "Sao necessarias pelo menos 10 analises validas.</div>",
        unsafe_allow_html=True,
    )

with st.sidebar.expander("Detalhes do treinamento"):
    st.write(f"Lotes totais: {metricas_ia['n']}")
    st.write(f"Lotes usados no resíduo: {metricas_ia['n_residuo']}")
    st.write(f"R² resíduo (treino): {metricas_ia['r2_residuo_treino']}")
    if metricas_ia["mae_residuo_validacao"] is not None:
        st.write(
            "Erro médio na validação temporal: "
            f"{metricas_ia['mae_residuo_validacao']:.2f} pontos percentuais"
        )
    st.write(f"R² retração: {metricas_ia['r2_retracao']}")
    st.markdown("**Peso (modelo físico calibrado)**")
    st.write(f"Lotes válidos: {metricas_ia['n_peso']}")
    st.write(f"R² peso: {metricas_ia['r2_peso']}")
    if metricas_ia["mae_peso_g"] is not None:
        st.write(f"Erro médio do peso: {metricas_ia['mae_peso_g']:.0f} g")
    st.caption(
        f"Peso = peso padrão × (parede ÷ {PAREDE_PADRAO_CM:.2f}) × "
        "(comprimento ÷ comprimento ideal) × fator do produto. "
        "Mais parede ou mais comprimento sempre aumentam o peso previsto."
    )

with st.sidebar.expander("Calibração do peso por produto"):
    por_produto = calibracao_peso.get("por_produto", {}) if calibracao_peso else {}
    if not por_produto:
        st.info("Ainda não há lotes suficientes para calibrar.")
    else:
        linhas = []
        for codigo, info in sorted(por_produto.items()):
            linhas.append({
                "Produto": codigo,
                "Fator": round(info["fator"], 3),
                "Origem": info["origem"],
                "Lotes válidos": info["n_validos"],
                "Descartados": info["n_descartados"],
                "Erro médio (g)": (round(info["mae_g"]) if info["mae_g"] is not None else None),
            })
        st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)
        st.caption(
            "Descartados = lotes cujo peso destoa muito da referência do produto "
            f"(razão fora de {RAZAO_MIN_VALIDA:.2f}–{RAZAO_MAX_VALIDA:.2f}). "
            "Revise esses registros no histórico."
        )


# ============================================================
# PREVISAO DE RESIDUO E CASOS SEMELHANTES
# ============================================================

def encontrar_casos_semelhantes(df, pct_amarelo, pct_branco, umidade, limite=8):
    if df is None or len(df) == 0:
        return pd.DataFrame()

    colunas_necessarias = ["pct_amarelo_ia", "pct_branco_ia", "umidade", "residuo", "data_dt"]
    if not all(coluna in df.columns for coluna in colunas_necessarias):
        return pd.DataFrame()

    base = df.dropna(subset=colunas_necessarias).copy()
    if len(base) == 0:
        return base

    base["distancia_ia"] = (
        abs(base["pct_amarelo_ia"] - pct_amarelo) * 100 * 1.5
        + abs(base["pct_branco_ia"] - pct_branco) * 100 * 2.0
        + abs(base["umidade"] - umidade) * 0.25
    )

    data_maxima = base["data_dt"].max()
    base["idade_dias"] = (data_maxima - base["data_dt"]).dt.days.clip(lower=0)
    base["score_vizinho"] = base["distancia_ia"] + base["idade_dias"] / 180.0

    base = base.sort_values(["score_vizinho", "data_dt"], ascending=[True, False])
    return base.head(limite)


def prever_residuo_inteligente(modelo, df, pct_amarelo, pct_branco, umidade):
    if modelo is None:
        raise ValueError("Modelo de residuo indisponivel.")

    X = pd.DataFrame([{"pct_amarelo_ia": pct_amarelo, "pct_branco_ia": pct_branco, "umidade": umidade}])
    pred_ml = float(modelo.predict(X)[0])

    vizinhos = encontrar_casos_semelhantes(df, pct_amarelo, pct_branco, umidade, limite=8)

    if len(vizinhos) > 0:
        vizinhos_fortes = vizinhos[vizinhos["distancia_ia"] <= 3.0].copy()
    else:
        vizinhos_fortes = pd.DataFrame()

    if len(vizinhos_fortes) >= 2:
        pesos_vizinhos = 1.0 / (0.5 + vizinhos_fortes["distancia_ia"])
        media_local = float(np.average(vizinhos_fortes["residuo"], weights=pesos_vizinhos))
        pred_final = 0.35 * pred_ml + 0.65 * media_local
        confianca = "ALTA" if len(vizinhos_fortes) >= 4 else "MEDIA"
    else:
        media_local = None
        pred_final = pred_ml
        confianca = "BAIXA"

    return pred_final, pred_ml, media_local, confianca, vizinhos


# ============================================================
# WHATSAPP - ANALISES REGISTRADAS
# ============================================================

def descricao_receita_lote(row):
    modo = texto_seguro(row.get("modo"), "Unica")
    p_a = inteiro_seguro(row.get("preto_a"))
    a_a = inteiro_seguro(row.get("amarelo_a"))
    b_a = inteiro_seguro(row.get("branco_a"))
    p_b = inteiro_seguro(row.get("preto_b"), p_a)
    a_b = inteiro_seguro(row.get("amarelo_b"), a_a)
    b_b = inteiro_seguro(row.get("branco_b"), b_a)

    if modo.lower().startswith("unica"):
        return f"{p_a} Preto + {a_a} Amarelo + {b_a} Branco"
    return f"A({p_a}/{a_a}/{b_a}) + B({p_b}/{a_b}/{b_b})"


def gerar_mensagem_analises(df, indices):
    quantidade = len(indices)
    linhas = [
        "*CeramicaIA - Relatorio de Analises*",
        "",
        f"{quantidade} analise selecionada" if quantidade == 1 else f"{quantidade} analises selecionadas",
        "",
    ]

    for ordem, indice in enumerate(indices, start=1):
        row = df.loc[indice]
        pct_preto, pct_amarelo, pct_branco = percentuais_da_linha(row)
        residuo = numero_seguro(row.get("residuo"))
        observacoes = texto_seguro(row.get("observacoes"))

        linhas.extend([
            f"*Analise {ordem} - {formatar_data(row.get('data'))}*",
            f"Produto: {texto_seguro(row.get('tipo_bloco'), '-')}",
            f"Producao: {texto_seguro(row.get('modo'), '-')}",
            (
                f"Barros: Preto {texto_seguro(row.get('cod_barro_preto'), '-')} | "
                f"Amarelo {codigo_opcional(row.get('cod_barro_amarelo'))} | "
                f"Branco {codigo_opcional(row.get('cod_barro_branco'))}"
            ),
            f"Receita: {descricao_receita_lote(row)}",
            (
                f"Composicao: {pct_preto * 100:.1f}% Preto | "
                f"{pct_amarelo * 100:.1f}% Amarelo | {pct_branco * 100:.1f}% Branco"
            ),
            f"Umidade: {formatar_numero(row.get('umidade'), 1)}%",
            f"Residuo real: {formatar_numero(residuo, 1)}% ({classificar_residuo(residuo)})",
            f"Retracao: {formatar_numero(row.get('retracao'), 1)}%",
            f"Parede: {formatar_numero(row.get('esp_parede'), 2)} cm",
            f"Comprimento: {formatar_numero(row.get('comprimento'), 1)} cm",
            f"Peso: {formatar_numero(row.get('peso'), 3)} kg",
        ])

        if observacoes:
            linhas.append(f"Observacoes: {observacoes}")

        linhas.extend(["", "------------------------------", ""])

    linhas.append("Relatorio gerado pelo CeramicaIA")
    return "\n".join(linhas)


# ============================================================
# ABA 1 - DIAGNOSTICO
# ============================================================

def renderizar_diagnostico():
    st.header("Diagnostico e Previsao")

    produtos_ativos = st.session_state.catalogo_produtos[
        st.session_state.catalogo_produtos["status"] == "Ativo"
    ].copy()

    if len(produtos_ativos) == 0:
        st.error("Nenhum produto ativo cadastrado.")
        return

    st.sidebar.header("Configuracoes do Lote")

    produto_selecionado = st.sidebar.selectbox(
        "Produto em producao:", produtos_ativos["chave_comercial"].tolist(), key="diag_produto",
    )
    dados_produto = produtos_ativos[produtos_ativos["chave_comercial"] == produto_selecionado].iloc[0]

    comp_verde_ideal = numero_seguro(dados_produto["comp_seco_ideal"], 20.0)
    peso_padrao = numero_seguro(dados_produto["peso_padrao"], 2.8)
    codigo_produto = texto_seguro(dados_produto["codigo"])

    st.sidebar.info(
        f"Peso padrao: {peso_padrao:.3f} kg\n\n"
        f"Comprimento verde ideal: {comp_verde_ideal:.1f} cm\n\n"
        f"Parede de referencia: {PAREDE_PADRAO_CM:.2f} cm"
    )

    barros_ativos = st.session_state.catalogo_barros[
        st.session_state.catalogo_barros["status"] == "Ativo"
    ].copy()

    barros_pretos = barros_ativos[barros_ativos["tipo_base"] == "Preto"]["codigo"].tolist()
    barros_amarelos = ["Nenhum"] + barros_ativos[barros_ativos["tipo_base"] == "Amarelo"]["codigo"].tolist()
    barros_brancos = ["Nenhum"] + barros_ativos[barros_ativos["tipo_base"] == "Branco"]["codigo"].tolist()

    if len(barros_pretos) == 0:
        st.error("Cadastre ou ative pelo menos um barro Preto.")
        return

    st.subheader("1. Selecao dos barros")

    cb1, cb2, cb3 = st.columns(3)
    with cb1:
        barro_preto = st.selectbox("Barro Argiloso (Forte):", barros_pretos, key="diag_barro_preto")
    with cb2:
        barro_amarelo = st.selectbox("Barro Intermediario (Medio):", barros_amarelos, key="diag_barro_amarelo")
    with cb3:
        barro_branco = st.selectbox("Barro Arenoso (Fraco):", barros_brancos, key="diag_barro_branco")

    st.divider()
    st.subheader("2. Composicao em conchas")
    st.caption(
        "Preencha as conchas usadas. Quando um barro nao for usado, selecione Nenhum ou informe zero."
    )

    modo = st.radio(
        "Tipo de producao:", ["Receita Unica", "Mistura Mesclada (Alternada)"],
        horizontal=True, key="diag_modo",
    )

    pct_preto = pct_amarelo = pct_branco = 0.0
    mistura_desc = ""
    composicao_ok = False

    if modo == "Receita Unica":
        c1, c2, c3 = st.columns(3)
        with c1:
            preto_a = st.number_input("Conchas de Preto", min_value=0, max_value=100, value=None, step=1, key="diag_preto_a")
        with c2:
            amarelo_a = st.number_input("Conchas de Amarelo", min_value=0, max_value=100, value=None, step=1, key="diag_amarelo_a")
        with c3:
            branco_a = st.number_input("Conchas de Branco", min_value=0, max_value=100, value=None, step=1, key="diag_branco_a")

        preto_a = concha_efetiva(preto_a, barro_preto)
        amarelo_a = concha_efetiva(amarelo_a, barro_amarelo)
        branco_a = concha_efetiva(branco_a, barro_branco)

        if campos_preenchidos(preto_a, amarelo_a, branco_a):
            pct_preto, pct_amarelo, pct_branco = calcular_percentuais_receita(
                "Unica", preto_a, amarelo_a, branco_a, preto_a, amarelo_a, branco_a
            )
            composicao_ok = (preto_a + amarelo_a + branco_a) > 0
            mistura_desc = f"{preto_a} Preto + {amarelo_a} Amarelo + {branco_a} Branco"
    else:
        st.markdown("**Receita A**")
        c1, c2, c3 = st.columns(3)
        with c1:
            preto_a = st.number_input("Preto (A)", min_value=0, max_value=100, value=None, step=1, key="diag_preto_a_m")
        with c2:
            amarelo_a = st.number_input("Amarelo (A)", min_value=0, max_value=100, value=None, step=1, key="diag_amarelo_a_m")
        with c3:
            branco_a = st.number_input("Branco (A)", min_value=0, max_value=100, value=None, step=1, key="diag_branco_a_m")

        st.markdown("**Receita B**")
        c4, c5, c6 = st.columns(3)
        with c4:
            preto_b = st.number_input("Preto (B)", min_value=0, max_value=100, value=None, step=1, key="diag_preto_b_m")
        with c5:
            amarelo_b = st.number_input("Amarelo (B)", min_value=0, max_value=100, value=None, step=1, key="diag_amarelo_b_m")
        with c6:
            branco_b = st.number_input("Branco (B)", min_value=0, max_value=100, value=None, step=1, key="diag_branco_b_m")

        preto_a = concha_efetiva(preto_a, barro_preto)
        amarelo_a = concha_efetiva(amarelo_a, barro_amarelo)
        branco_a = concha_efetiva(branco_a, barro_branco)
        preto_b = concha_efetiva(preto_b, barro_preto)
        amarelo_b = concha_efetiva(amarelo_b, barro_amarelo)
        branco_b = concha_efetiva(branco_b, barro_branco)

        if campos_preenchidos(preto_a, amarelo_a, branco_a, preto_b, amarelo_b, branco_b):
            pct_preto, pct_amarelo, pct_branco = calcular_percentuais_receita(
                "Mesclada", preto_a, amarelo_a, branco_a, preto_b, amarelo_b, branco_b
            )
            composicao_ok = (preto_a + amarelo_a + branco_a + preto_b + amarelo_b + branco_b) > 0
            mistura_desc = f"A({preto_a}/{amarelo_a}/{branco_a}) + B({preto_b}/{amarelo_b}/{branco_b})"

    if composicao_ok:
        st.info(
            f"Composicao calculada: {pct_preto * 100:.2f}% Preto | "
            f"{pct_amarelo * 100:.2f}% Amarelo | {pct_branco * 100:.2f}% Branco"
        )
    else:
        st.warning("Preencha uma receita com pelo menos uma concha.")

    st.divider()
    st.subheader("3. Processo e dimensoes")

    cu, ce, cc = st.columns(3)
    with cu:
        umidade = st.number_input("Umidade da massa (%)", min_value=0.0, max_value=40.0, value=None, step=0.1, key="diag_umidade")
    with ce:
        esp_parede = st.number_input("Espessura da parede (cm)", min_value=0.0, max_value=5.0, value=None, step=0.01, key="diag_parede")
    with cc:
        comprimento_cm = st.number_input("Comprimento verde (cm)", min_value=0.0, max_value=100.0, value=None, step=0.1, key="diag_comprimento")

    parametros_ok = campos_preenchidos(umidade, esp_parede, comprimento_cm)
    if parametros_ok and (esp_parede <= 0 or comprimento_cm <= 0):
        parametros_ok = False
        st.warning("Parede e comprimento precisam ser maiores que zero.")

    st.divider()

    if st.button("GERAR DIAGNOSTICO DO LOTE", type="primary", use_container_width=True, key="botao_diagnostico"):
        if not IA_RESIDUO_DISPONIVEL:
            st.session_state.diagnostico_gerado = False
            st.error("A IA de residuo ainda nao possui dados suficientes.")
        elif not composicao_ok:
            st.session_state.diagnostico_gerado = False
            st.error("Preencha corretamente a composicao da receita.")
        elif not parametros_ok:
            st.session_state.diagnostico_gerado = False
            st.error("Preencha umidade, parede e comprimento.")
        else:
            st.session_state.diagnostico_gerado = True

    pode_diagnosticar = (
        st.session_state.diagnostico_gerado and IA_RESIDUO_DISPONIVEL and composicao_ok and parametros_ok
    )
    if not pode_diagnosticar:
        return

    (pred_res, pred_res_ml, media_local, confianca_res, vizinhos) = prever_residuo_inteligente(
        m_res, df_treino_ia, pct_amarelo, pct_branco, umidade,
    )

    # Peso: modelo fisico calibrado por produto
    pred_peso, peso_base, fator_peso, info_peso = prever_peso(
        calibracao_peso, codigo_produto, peso_padrao, comp_verde_ideal, esp_parede, comprimento_cm,
    )

    X_retracao = pd.DataFrame([{
        "pct_preto_ia": pct_preto, "pct_amarelo_ia": pct_amarelo, "pct_branco_ia": pct_branco,
        "umidade": umidade, "esp_parede": esp_parede,
    }])
    pred_retracao = float(m_ret.predict(X_retracao)[0]) if m_ret is not None else 3.0

    st.divider()
    st.subheader("Resultados previstos")

    diferenca_comprimento = comprimento_cm - comp_verde_ideal
    if diferenca_comprimento > 0.15:
        st.warning(f"Comprimento {diferenca_comprimento * 10:.0f} mm acima do ideal.")
    elif diferenca_comprimento < -0.15:
        st.warning(f"Comprimento {abs(diferenca_comprimento) * 10:.0f} mm abaixo do ideal.")

    r1, r2, r3 = st.columns(3)

    with r1:
        st.metric("Residuo previsto", f"{pred_res:.1f}%")
        if pred_res > 32:
            st.error("BLOCO FRACO / ARENOSO")
        elif pred_res < 28:
            st.warning("BLOCO FORTE / ARGILOSO")
        else:
            st.success("FAIXA IDEAL")
        st.caption(f"Confianca: {confianca_res}")

    with r2:
        st.metric("Retracao prevista", f"{pred_retracao:.1f}%")
        comprimento_estimado = comprimento_cm * (1 - pred_retracao / 100)
        st.caption(f"Comprimento estimado: {comprimento_estimado:.1f} cm")

    excesso_g = (pred_peso - peso_padrao) * 1000

    with r3:
        st.metric(
            "Peso previsto", f"{pred_peso:.3f} kg",
            delta=f"{excesso_g:+.0f} g em relacao ao padrao", delta_color="inverse",
        )
        if excesso_g > 50:
            st.error("ACIMA DO PADRAO")
        elif excesso_g < -50:
            st.warning("ABAIXO DO PADRAO")
        else:
            st.success("DENTRO DO PADRAO")

    with st.expander("Entenda a previsao de residuo"):
        st.write(f"Previsao geral do modelo: {pred_res_ml:.2f}%")
        if media_local is not None:
            st.write(f"Media ponderada dos lotes semelhantes: {media_local:.2f}%")
        st.write(f"Previsao final: {pred_res:.2f}%")
        st.write(f"Confianca: {confianca_res}")

        if len(vizinhos) > 0:
            vizinhos_exibir = vizinhos[
                ["data", "modo", "pct_preto_ia", "pct_amarelo_ia", "pct_branco_ia", "umidade", "residuo"]
            ].copy()
            vizinhos_exibir.columns = ["Data", "Modo", "% Preto", "% Amarelo", "% Branco", "Umidade", "Residuo Real"]
            for coluna in ["% Preto", "% Amarelo", "% Branco"]:
                vizinhos_exibir[coluna] *= 100
            st.dataframe(vizinhos_exibir, use_container_width=True, hide_index=True)

    with st.expander("Entenda a previsao de peso"):
        st.write(
            f"Peso base = {peso_padrao:.3f} kg × ({esp_parede:.2f} ÷ {PAREDE_PADRAO_CM:.2f}) × "
            f"({comprimento_cm:.1f} ÷ {comp_verde_ideal:.1f}) = **{peso_base:.3f} kg**"
        )
        if info_peso and info_peso["origem"] == "calibrado":
            st.write(
                f"Fator de calibracao do produto {codigo_produto}: **{fator_peso:.3f}** "
                f"(baseado em {info_peso['n_validos']} lotes reais; erro medio de "
                f"{info_peso['mae_g']:.0f} g)"
            )
        else:
            st.write(
                f"Fator de calibracao: **1,000** (produto {codigo_produto} ainda nao tem "
                f"{MIN_REGISTROS_CALIBRACAO} lotes validos; usando formula pura)."
            )
        st.write(f"Peso previsto = {peso_base:.3f} × {fator_peso:.3f} = **{pred_peso:.3f} kg**")
        st.caption(
            "Este calculo e proporcional: aumentar a parede ou o comprimento sempre aumenta o peso previsto."
        )

    texto_financeiro_whatsapp = ""

    if excesso_g > 0:
        st.divider()
        st.subheader("Impacto financeiro do excesso de massa")

        cp, cc2 = st.columns(2)
        with cp:
            producao_dia = st.number_input(
                "Producao planejada por dia:", min_value=1, max_value=1000000, value=None, step=1000, key="diag_producao_dia",
            )
        with cc2:
            custo_tonelada = st.number_input(
                "Custo da tonelada (R$):", min_value=0.0, max_value=100000.0, value=None, step=1.0, key="diag_custo_tonelada",
            )

        if campos_preenchidos(producao_dia, custo_tonelada):
            toneladas_perdidas_dia = excesso_g / 1000 * producao_dia / 1000
            prejuizo_dia = toneladas_perdidas_dia * custo_tonelada
            prejuizo_mes = prejuizo_dia * DIAS_PRODUCAO_MES

            st.error(
                f"Desperdicio: {toneladas_perdidas_dia:.2f} toneladas/dia\n\n"
                f"Custo diario: R$ {prejuizo_dia:,.2f}\n\n"
                f"Impacto mensal ({DIAS_PRODUCAO_MES} dias): R$ {prejuizo_mes:,.2f}"
            )
            texto_financeiro_whatsapp = (
                f"\nPerda estimada: {toneladas_perdidas_dia:.2f} ton/dia"
                f"\nImpacto mensal ({DIAS_PRODUCAO_MES} dias): R$ {prejuizo_mes:,.2f}"
            )
        else:
            st.info("Preencha a producao e o custo da tonelada para calcular o impacto.")

    st.divider()

    mensagem_diagnostico = (
        "*CeramicaIA - Diagnostico*\n\n"
        f"Produto: {codigo_produto}\n"
        f"Mistura: {mistura_desc}\n"
        f"Preto: {pct_preto * 100:.1f}%\n"
        f"Amarelo: {pct_amarelo * 100:.1f}%\n"
        f"Branco: {pct_branco * 100:.1f}%\n"
        f"Umidade: {umidade:.1f}%\n"
        f"Parede: {esp_parede:.2f} cm\n"
        f"Comprimento: {comprimento_cm:.1f} cm\n\n"
        f"Residuo previsto: {pred_res:.1f}%\n"
        f"Confianca: {confianca_res}\n"
        f"Retracao prevista: {pred_retracao:.1f}%\n"
        f"Peso previsto: {pred_peso:.3f} kg"
        f"{texto_financeiro_whatsapp}\n\n"
        "Gerado pelo CeramicaIA"
    )
    url_whatsapp = "https://wa.me/?text=" + urllib.parse.quote(mensagem_diagnostico)
    st.link_button("Compartilhar diagnostico no WhatsApp", url_whatsapp, use_container_width=True)


# ============================================================
# COMPARTILHAMENTO DE ANALISES REGISTRADAS
# ============================================================

def renderizar_compartilhamento_lotes():
    st.subheader("Compartilhar analises pelo WhatsApp")
    st.caption("Selecione uma ou varias analises. Voce pode digitar a data no campo de busca da selecao.")

    df_lotes = st.session_state.df_master
    if len(df_lotes) == 0:
        st.info("Ainda nao existem analises para compartilhar.")
        return

    indices_selecionados = st.multiselect(
        "Analises que serao compartilhadas:",
        options=df_lotes.index.tolist(),
        format_func=lambda indice: rotulo_lote(indice, df_lotes.loc[indice]),
        key="lotes_whatsapp",
        placeholder="Clique para selecionar uma ou mais analises",
    )

    if not indices_selecionados:
        st.info("Selecione pelo menos uma analise.")
        return

    mensagem = gerar_mensagem_analises(df_lotes, indices_selecionados)

    if len(mensagem) > 7000:
        st.warning(
            "A mensagem ficou muito extensa. Dependendo do aparelho, o WhatsApp pode limitar o texto. "
            "Se necessario, compartilhe em grupos menores."
        )

    with st.expander("Visualizar mensagem antes de compartilhar"):
        st.text_area("Mensagem:", value=mensagem, height=350, disabled=True, key="preview_whatsapp_lotes")

    url_whatsapp = "https://wa.me/?text=" + urllib.parse.quote(mensagem)
    rotulo_botao = (
        "Compartilhar 1 analise no WhatsApp"
        if len(indices_selecionados) == 1
        else f"Compartilhar {len(indices_selecionados)} analises no WhatsApp"
    )
    st.link_button(rotulo_botao, url_whatsapp, use_container_width=True)


# ============================================================
# GERENCIAMENTO DE LOTES
# ============================================================

def renderizar_gerenciamento_lotes():
    df_lotes = st.session_state.df_master
    if len(df_lotes) == 0:
        return

    with st.expander("Editar ou excluir uma analise cadastrada"):
        indice_lote = st.selectbox(
            "Selecione a analise:",
            options=df_lotes.index.tolist(),
            format_func=lambda indice: rotulo_lote(indice, df_lotes.loc[indice]),
            key="gerenciar_lote_selecionado",
        )
        lote_atual = df_lotes.loc[indice_lote]

        catalogo_produtos = st.session_state.catalogo_produtos
        codigos_produtos = catalogo_produtos["codigo"].astype(str).tolist()
        codigo_produto_atual = texto_seguro(lote_atual.get("tipo_bloco"))
        codigos_produtos = adicionar_opcao_atual(codigos_produtos, codigo_produto_atual)
        if not codigo_produto_atual and codigos_produtos:
            codigo_produto_atual = codigos_produtos[0]
        mapa_produtos = dict(zip(
            catalogo_produtos["codigo"].astype(str), catalogo_produtos["chave_comercial"].astype(str),
        ))

        catalogo_barros = st.session_state.catalogo_barros
        pretos = catalogo_barros[catalogo_barros["tipo_base"] == "Preto"]["codigo"].astype(str).tolist()
        amarelos = ["Nenhum"] + catalogo_barros[catalogo_barros["tipo_base"] == "Amarelo"]["codigo"].astype(str).tolist()
        brancos = ["Nenhum"] + catalogo_barros[catalogo_barros["tipo_base"] == "Branco"]["codigo"].astype(str).tolist()

        codigo_preto_atual = texto_seguro(lote_atual.get("cod_barro_preto"))
        codigo_amarelo_atual = codigo_opcional(lote_atual.get("cod_barro_amarelo"))
        codigo_branco_atual = codigo_opcional(lote_atual.get("cod_barro_branco"))

        pretos = adicionar_opcao_atual(pretos, codigo_preto_atual)
        if not codigo_preto_atual and pretos:
            codigo_preto_atual = pretos[0]
        amarelos = adicionar_opcao_atual(amarelos, codigo_amarelo_atual)
        brancos = adicionar_opcao_atual(brancos, codigo_branco_atual)

        with st.form("form_editar_lote"):
            st.markdown("**Identificacao**")
            e1, e2, e3 = st.columns(3)
            with e1:
                edit_data = st.date_input("Data da analise:", value=data_segura(lote_atual.get("data")))
            with e2:
                edit_produto = st.selectbox(
                    "Produto:", options=codigos_produtos,
                    index=codigos_produtos.index(codigo_produto_atual) if codigo_produto_atual in codigos_produtos else 0,
                    format_func=lambda codigo: mapa_produtos.get(codigo, codigo),
                )
            with e3:
                modos = ["Unica", "Mesclada"]
                modo_atual = texto_seguro(lote_atual.get("modo"), "Unica")
                edit_modo = st.selectbox(
                    "Tipo de producao:", modos, index=modos.index(modo_atual) if modo_atual in modos else 0,
                )

            b1, b2, b3 = st.columns(3)
            with b1:
                edit_codigo_preto = st.selectbox(
                    "Barro Preto:", pretos, index=pretos.index(codigo_preto_atual) if codigo_preto_atual in pretos else 0,
                )
            with b2:
                edit_codigo_amarelo = st.selectbox("Barro Amarelo:", amarelos, index=amarelos.index(codigo_amarelo_atual))
            with b3:
                edit_codigo_branco = st.selectbox("Barro Branco:", brancos, index=brancos.index(codigo_branco_atual))

            st.markdown("**Receitas**")
            ra, rb = st.columns(2)
            with ra:
                st.caption("Receita A")
                edit_preto_a = st.number_input("Preto A", min_value=0, value=inteiro_seguro(lote_atual.get("preto_a")), step=1)
                edit_amarelo_a = st.number_input("Amarelo A", min_value=0, value=inteiro_seguro(lote_atual.get("amarelo_a")), step=1)
                edit_branco_a = st.number_input("Branco A", min_value=0, value=inteiro_seguro(lote_atual.get("branco_a")), step=1)
            with rb:
                st.caption("Receita B")
                edit_preto_b = st.number_input("Preto B", min_value=0, value=inteiro_seguro(lote_atual.get("preto_b")), step=1)
                edit_amarelo_b = st.number_input("Amarelo B", min_value=0, value=inteiro_seguro(lote_atual.get("amarelo_b")), step=1)
                edit_branco_b = st.number_input("Branco B", min_value=0, value=inteiro_seguro(lote_atual.get("branco_b")), step=1)

            st.markdown("**Resultados reais**")
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                edit_umidade = st.number_input("Umidade (%)", min_value=0.0, value=numero_seguro(lote_atual.get("umidade")), step=0.1)
            with m2:
                edit_residuo = st.number_input("Residuo (%)", min_value=0.0, value=numero_seguro(lote_atual.get("residuo")), step=0.1)
            with m3:
                edit_retracao = st.number_input("Retracao (%)", min_value=0.0, value=numero_seguro(lote_atual.get("retracao")), step=0.1)
            with m4:
                edit_parede = st.number_input("Parede (cm)", min_value=0.0, value=numero_seguro(lote_atual.get("esp_parede")), step=0.01)

            m5, m6 = st.columns(2)
            with m5:
                edit_comprimento = st.number_input("Comprimento (cm)", min_value=0.0, value=numero_seguro(lote_atual.get("comprimento")), step=0.1)
            with m6:
                edit_peso = st.number_input("Peso (kg)", min_value=0.0, value=numero_seguro(lote_atual.get("peso")), step=0.001, format="%.3f")

            edit_observacoes = st.text_area("Observacoes:", value=texto_seguro(lote_atual.get("observacoes")))

            salvar_edicao = st.form_submit_button("Salvar alteracoes", type="primary", use_container_width=True)

        if salvar_edicao:
            edit_amarelo_a = concha_efetiva(edit_amarelo_a, edit_codigo_amarelo)
            edit_branco_a = concha_efetiva(edit_branco_a, edit_codigo_branco)
            edit_amarelo_b = concha_efetiva(edit_amarelo_b, edit_codigo_amarelo)
            edit_branco_b = concha_efetiva(edit_branco_b, edit_codigo_branco)

            if edit_modo == "Unica":
                preto_b_salvar, amarelo_b_salvar, branco_b_salvar = edit_preto_a, edit_amarelo_a, edit_branco_a
            else:
                preto_b_salvar, amarelo_b_salvar, branco_b_salvar = edit_preto_b, edit_amarelo_b, edit_branco_b

            total_conchas = edit_preto_a + edit_amarelo_a + edit_branco_a
            if edit_modo == "Mesclada":
                total_conchas += preto_b_salvar + amarelo_b_salvar + branco_b_salvar

            if total_conchas <= 0:
                st.error("A receita precisa ter pelo menos uma concha.")
            else:
                pct_preto, pct_amarelo, pct_branco = calcular_percentuais_receita(
                    edit_modo, edit_preto_a, edit_amarelo_a, edit_branco_a,
                    preto_b_salvar, amarelo_b_salvar, branco_b_salvar,
                )

                produto_encontrado = catalogo_produtos[catalogo_produtos["codigo"].astype(str) == edit_produto]
                if len(produto_encontrado) > 0:
                    peso_meta = numero_seguro(produto_encontrado.iloc[0]["peso_padrao"])
                else:
                    peso_meta = edit_peso - numero_seguro(lote_atual.get("excesso_peso")) / 1000

                excesso = (edit_peso - peso_meta) * 1000

                atualizacoes = {
                    "data": edit_data.strftime("%Y-%m-%d"), "modo": edit_modo,
                    "cod_barro_preto": edit_codigo_preto, "cod_barro_amarelo": edit_codigo_amarelo,
                    "cod_barro_branco": edit_codigo_branco,
                    "preto_a": edit_preto_a, "amarelo_a": edit_amarelo_a, "branco_a": edit_branco_a,
                    "preto_b": preto_b_salvar, "amarelo_b": amarelo_b_salvar, "branco_b": branco_b_salvar,
                    "pct_preto": round(pct_preto, 4), "pct_amarelo": round(pct_amarelo, 4),
                    "pct_branco": round(pct_branco, 4),
                    "umidade": edit_umidade, "residuo": edit_residuo, "retracao": edit_retracao,
                    "esp_parede": edit_parede, "peso": edit_peso, "comprimento": edit_comprimento,
                    "tipo_bloco": edit_produto, "class_residuo": classe_residuo_banco(edit_residuo),
                    "excesso_peso": round(excesso, 0), "observacoes": edit_observacoes,
                }
                for coluna, valor in atualizacoes.items():
                    st.session_state.df_master.at[indice_lote, coluna] = valor

                if persistir_dados("lotes"):
                    st.success("Analise atualizada.")
                    st.rerun()

        st.divider()

        confirmar_exclusao = st.checkbox(
            "Confirmo a exclusao definitiva desta analise", key=f"confirmar_exclusao_lote_{indice_lote}",
        )
        if st.button("Excluir analise selecionada", key=f"excluir_lote_{indice_lote}", use_container_width=True):
            if not confirmar_exclusao:
                st.error("Marque a confirmacao antes de excluir.")
            else:
                st.session_state.df_master = (
                    st.session_state.df_master.drop(index=indice_lote).reset_index(drop=True)
                )
                st.session_state.pop("lotes_whatsapp", None)
                if persistir_dados("lotes"):
                    st.success("Analise excluida.")
                    st.rerun()


# ============================================================
# ABA 2 - REGISTRO DE ANALISES
# ============================================================

def renderizar_registro_lotes():
    st.header("Registrar Analise de Mistura")
    st.caption("Cada resultado salvo passa a fazer parte do aprendizado da IA de residuo.")

    barros_ativos = st.session_state.catalogo_barros[st.session_state.catalogo_barros["status"] == "Ativo"]
    produtos_ativos = st.session_state.catalogo_produtos[st.session_state.catalogo_produtos["status"] == "Ativo"]

    pretos = barros_ativos[barros_ativos["tipo_base"] == "Preto"]["codigo"].tolist()
    amarelos = ["Nenhum"] + barros_ativos[barros_ativos["tipo_base"] == "Amarelo"]["codigo"].tolist()
    brancos = ["Nenhum"] + barros_ativos[barros_ativos["tipo_base"] == "Branco"]["codigo"].tolist()

    if len(produtos_ativos) == 0 or len(pretos) == 0:
        st.warning("Para registrar uma nova analise, mantenha pelo menos um produto e um barro Preto ativos.")
    else:
        with st.form("form_registro_lote", clear_on_submit=True):
            st.subheader("1. Identificacao")
            c1, c2, c3 = st.columns(3)
            with c1:
                data_lote = st.date_input("Data da analise:", value=date.today())
                produto_lote = st.selectbox("Produto:", produtos_ativos["chave_comercial"].tolist())

            produto_row = produtos_ativos[produtos_ativos["chave_comercial"] == produto_lote].iloc[0]
            codigo_produto = texto_seguro(produto_row["codigo"])
            peso_meta = numero_seguro(produto_row["peso_padrao"])

            with c2:
                codigo_preto = st.selectbox("Barro Preto:", pretos)
                codigo_amarelo = st.selectbox("Barro Amarelo:", amarelos)
                codigo_branco = st.selectbox("Barro Branco:", brancos)
            with c3:
                modo_lote = st.selectbox("Tipo de producao:", ["Unica", "Mesclada"])

            st.subheader("2. Quantidade de conchas")
            ra, rb = st.columns(2)
            with ra:
                st.caption("Receita A")
                p_a = st.number_input("Preto A", min_value=0, max_value=100, value=None, step=1)
                a_a = st.number_input("Amarelo A", min_value=0, max_value=100, value=None, step=1)
                b_a = st.number_input("Branco A", min_value=0, max_value=100, value=None, step=1)
            with rb:
                st.caption("Receita B - somente para Mesclada")
                p_b = st.number_input("Preto B", min_value=0, max_value=100, value=None, step=1)
                a_b = st.number_input("Amarelo B", min_value=0, max_value=100, value=None, step=1)
                b_b = st.number_input("Branco B", min_value=0, max_value=100, value=None, step=1)

            st.subheader("3. Resultados reais")
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                umidade_real = st.number_input("Umidade (%)", min_value=0.0, max_value=100.0, value=None, step=0.1)
            with m2:
                residuo_real = st.number_input("Residuo (%)", min_value=0.0, max_value=100.0, value=None, step=0.1)
            with m3:
                retracao_real = st.number_input("Retracao (%)", min_value=0.0, max_value=100.0, value=None, step=0.1)
            with m4:
                parede_real = st.number_input("Espessura da parede (cm)", min_value=0.0, max_value=10.0, value=None, step=0.01)

            m5, m6 = st.columns(2)
            with m5:
                comprimento_real = st.number_input("Comprimento verde (cm)", min_value=0.0, max_value=100.0, value=None, step=0.1)
            with m6:
                peso_real = st.number_input("Peso real (kg)", min_value=0.0, max_value=100.0, value=None, step=0.001, format="%.3f")

            observacoes = st.text_area("Observacoes:", value="")

            salvar_lote = st.form_submit_button("Salvar registro e recalibrar IA", type="primary", use_container_width=True)

        if salvar_lote:
            p_a = concha_efetiva(p_a, codigo_preto)
            a_a = concha_efetiva(a_a, codigo_amarelo)
            b_a = concha_efetiva(b_a, codigo_branco)
            p_b = concha_efetiva(p_b, codigo_preto)
            a_b = concha_efetiva(a_b, codigo_amarelo)
            b_b = concha_efetiva(b_b, codigo_branco)

            obrigatorios = [p_a, a_a, b_a, umidade_real, residuo_real, retracao_real, parede_real, comprimento_real, peso_real]
            if modo_lote == "Mesclada":
                obrigatorios.extend([p_b, a_b, b_b])

            if not campos_preenchidos(*obrigatorios):
                st.error("Preencha todos os campos numericos obrigatorios. Quando um barro nao for usado, informe zero.")
            else:
                if modo_lote == "Unica":
                    p_b_salvar, a_b_salvar, b_b_salvar = p_a, a_a, b_a
                else:
                    p_b_salvar, a_b_salvar, b_b_salvar = p_b, a_b, b_b

                total_conchas = p_a + a_a + b_a
                if modo_lote == "Mesclada":
                    total_conchas += p_b_salvar + a_b_salvar + b_b_salvar

                if total_conchas <= 0:
                    st.error("A receita precisa ter pelo menos uma concha.")
                else:
                    pct_preto, pct_amarelo, pct_branco = calcular_percentuais_receita(
                        modo_lote, p_a, a_a, b_a, p_b_salvar, a_b_salvar, b_b_salvar,
                    )

                    previsao_antes = None
                    confianca_antes = None
                    if IA_RESIDUO_DISPONIVEL:
                        (previsao_antes, _, _, confianca_antes, _) = prever_residuo_inteligente(
                            m_res, df_treino_ia, pct_amarelo, pct_branco, umidade_real,
                        )

                    excesso = (peso_real - peso_meta) * 1000

                    novo_registro = {
                        "data": data_lote.strftime("%Y-%m-%d"), "modo": modo_lote,
                        "cod_barro_preto": codigo_preto, "cod_barro_amarelo": codigo_amarelo,
                        "cod_barro_branco": codigo_branco,
                        "preto_a": p_a, "amarelo_a": a_a, "branco_a": b_a,
                        "preto_b": p_b_salvar, "amarelo_b": a_b_salvar, "branco_b": b_b_salvar,
                        "pct_preto": round(pct_preto, 4), "pct_amarelo": round(pct_amarelo, 4),
                        "pct_branco": round(pct_branco, 4),
                        "umidade": umidade_real, "residuo": residuo_real, "retracao": retracao_real,
                        "esp_parede": parede_real, "peso": peso_real, "comprimento": comprimento_real,
                        "tipo_bloco": codigo_produto, "class_residuo": classe_residuo_banco(residuo_real),
                        "excesso_peso": round(excesso, 0), "observacoes": observacoes,
                    }

                    st.session_state.df_master = pd.concat(
                        [pd.DataFrame([novo_registro]), st.session_state.df_master], ignore_index=True,
                    )

                    if persistir_dados("lotes"):
                        st.success("Analise salva. O resultado entrara no proximo treinamento da IA.")

                        if previsao_antes is not None:
                            erro = abs(residuo_real - previsao_antes)
                            st.subheader("Previsao anterior x resultado real")
                            cc1, cc2, cc3 = st.columns(3)
                            with cc1:
                                st.metric("Previsao anterior", f"{previsao_antes:.1f}%")
                            with cc2:
                                st.metric("Resultado real", f"{residuo_real:.1f}%")
                            with cc3:
                                st.metric("Erro", f"{erro:.1f} ponto(s) %")
                            st.caption(f"Confianca anterior: {confianca_antes}")

    st.divider()
    st.subheader("Historico de analises")
    st.write(f"Total registrado: {len(st.session_state.df_master)}")

    if len(st.session_state.df_master) > 0:
        st.dataframe(st.session_state.df_master, use_container_width=True, hide_index=True)
        csv_completo = st.session_state.df_master.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Baixar backup completo em CSV", data=csv_completo,
            file_name="ceramica_lotes_" + datetime.now().strftime("%Y%m%d") + ".csv",
            mime="text/csv", use_container_width=True,
        )
    else:
        st.info("Ainda nao existem analises cadastradas.")

    st.divider()
    renderizar_compartilhamento_lotes()
    st.divider()
    renderizar_gerenciamento_lotes()


# ============================================================
# ABA 3 - BARRO PURO
# ============================================================

def renderizar_barro_puro():
    st.header("Analise de Barro Puro")
    st.info(
        "Estas analises sao armazenadas para acompanhamento da materia-prima. "
        "Neste momento, elas ainda nao alteram a previsao da IA."
    )

    catalogo_barros = st.session_state.catalogo_barros
    codigos_ativos = catalogo_barros[catalogo_barros["status"] == "Ativo"]["codigo"].tolist()

    col_form, col_hist = st.columns([1, 2])

    with col_form:
        st.subheader("Nova analise")

        if len(codigos_ativos) == 0:
            st.warning("Nao existem barros ativos.")
        else:
            with st.form("form_barro_puro", clear_on_submit=True):
                data_puro = st.date_input("Data da amostra:", value=date.today())
                codigo_puro = st.selectbox("Barro:", codigos_ativos)
                peso_amostra = st.number_input("Peso da amostra seca (g)", min_value=0.0, max_value=100000.0, value=None, step=1.0)
                peso_residuo = st.number_input("Peso do residuo seco (g)", min_value=0.0, max_value=100000.0, value=None, step=1.0)

                if campos_preenchidos(peso_amostra, peso_residuo) and peso_amostra > 0:
                    st.info(f"Residuo puro calculado: {peso_residuo / peso_amostra * 100:.2f}%")

                observacoes_puro = st.text_area("Observacoes:", value="")
                salvar_puro = st.form_submit_button("Salvar analise de barro puro", type="primary", use_container_width=True)

            if salvar_puro:
                if not campos_preenchidos(peso_amostra, peso_residuo):
                    st.error("Preencha os dois pesos.")
                elif peso_amostra <= 0:
                    st.error("O peso da amostra precisa ser maior que zero.")
                elif peso_residuo > peso_amostra:
                    st.error("O peso do residuo nao pode ser maior que o peso da amostra.")
                else:
                    percentual_puro = peso_residuo / peso_amostra * 100
                    novo_registro = {
                        "data": data_puro.strftime("%Y-%m-%d"), "codigo_barro": codigo_puro,
                        "peso_amostra_g": peso_amostra, "peso_residuo_g": peso_residuo,
                        "pct_residuo_puro": round(percentual_puro, 2), "observacoes": observacoes_puro,
                    }
                    st.session_state.analises_puro = pd.concat(
                        [pd.DataFrame([novo_registro]), st.session_state.analises_puro], ignore_index=True,
                    )
                    if persistir_dados("puro"):
                        st.success("Analise de barro puro salva.")

    with col_hist:
        st.subheader("Historico")
        if len(st.session_state.analises_puro) > 0:
            st.dataframe(st.session_state.analises_puro, use_container_width=True, hide_index=True)
        else:
            st.info("Ainda nao existem analises de barro puro.")

    if len(st.session_state.analises_puro) == 0:
        return

    st.divider()

    with st.expander("Editar ou excluir uma analise de barro puro"):
        df_puro = st.session_state.analises_puro
        indice_puro = st.selectbox(
            "Selecione a analise:", options=df_puro.index.tolist(),
            format_func=lambda indice: rotulo_puro(indice, df_puro.loc[indice]),
            key="gerenciar_puro_selecionado",
        )
        analise_atual = df_puro.loc[indice_puro]

        todos_codigos = catalogo_barros["codigo"].astype(str).tolist()
        codigo_atual = texto_seguro(analise_atual.get("codigo_barro"))
        todos_codigos = adicionar_opcao_atual(todos_codigos, codigo_atual)
        if not codigo_atual and todos_codigos:
            codigo_atual = todos_codigos[0]

        with st.form("form_editar_puro"):
            edit_data = st.date_input("Data da amostra:", value=data_segura(analise_atual.get("data")))
            edit_codigo = st.selectbox(
                "Barro:", todos_codigos, index=todos_codigos.index(codigo_atual) if codigo_atual in todos_codigos else 0,
            )
            edit_peso_amostra = st.number_input(
                "Peso da amostra seca (g)", min_value=0.0, value=numero_seguro(analise_atual.get("peso_amostra_g")), step=1.0,
            )
            edit_peso_residuo = st.number_input(
                "Peso do residuo seco (g)", min_value=0.0, value=numero_seguro(analise_atual.get("peso_residuo_g")), step=1.0,
            )
            if edit_peso_amostra > 0:
                st.info(f"Residuo puro calculado: {edit_peso_residuo / edit_peso_amostra * 100:.2f}%")

            edit_observacoes = st.text_area("Observacoes:", value=texto_seguro(analise_atual.get("observacoes")))
            salvar_edicao = st.form_submit_button("Salvar alteracoes", type="primary", use_container_width=True)

        if salvar_edicao:
            if edit_peso_amostra <= 0:
                st.error("O peso da amostra precisa ser maior que zero.")
            elif edit_peso_residuo > edit_peso_amostra:
                st.error("O peso do residuo nao pode ser maior que o peso da amostra.")
            else:
                percentual = edit_peso_residuo / edit_peso_amostra * 100
                df = st.session_state.analises_puro
                df.at[indice_puro, "data"] = edit_data.strftime("%Y-%m-%d")
                df.at[indice_puro, "codigo_barro"] = edit_codigo
                df.at[indice_puro, "peso_amostra_g"] = edit_peso_amostra
                df.at[indice_puro, "peso_residuo_g"] = edit_peso_residuo
                df.at[indice_puro, "pct_residuo_puro"] = round(percentual, 2)
                df.at[indice_puro, "observacoes"] = edit_observacoes

                if persistir_dados("puro"):
                    st.success("Analise atualizada.")
                    st.rerun()

        st.divider()

        confirmar = st.checkbox(
            "Confirmo a exclusao definitiva desta analise", key=f"confirmar_exclusao_puro_{indice_puro}",
        )
        if st.button("Excluir analise selecionada", key=f"excluir_puro_{indice_puro}", use_container_width=True):
            if not confirmar:
                st.error("Marque a confirmacao antes de excluir.")
            else:
                st.session_state.analises_puro = (
                    st.session_state.analises_puro.drop(index=indice_puro).reset_index(drop=True)
                )
                if persistir_dados("puro"):
                    st.success("Analise excluida.")
                    st.rerun()


# ============================================================
# ABA 4 - CADASTRO DE BARROS
# ============================================================

def renderizar_barros():
    st.header("Cadastro e Controle de Barros / Jazidas")

    col_novo, col_edicao = st.columns(2)

    with col_novo:
        st.subheader("Cadastrar novo barro")

        with st.form("form_novo_barro", clear_on_submit=True):
            novo_codigo = st.text_input("Codigo oficial:", value="")
            novo_nome = st.text_input("Nome ou apelido:", value="")
            novo_tipo = st.selectbox("Tipo:", ["Preto", "Amarelo", "Branco"])
            nova_localidade = st.text_input("Localidade:", value="")
            novo_residuo = st.number_input(
                "Residuo puro de referencia (%)", min_value=0.0, max_value=100.0, value=None, step=0.1,
                help="Campo de acompanhamento. Ainda nao influencia a IA.",
            )
            cadastrar = st.form_submit_button("Cadastrar barro", type="primary", use_container_width=True)

        if cadastrar:
            codigo = novo_codigo.strip().upper()
            nome = novo_nome.strip()
            codigos_existentes = st.session_state.catalogo_barros["codigo"].astype(str).tolist()

            if not codigo or not nome:
                st.error("Informe o codigo e o nome.")
            elif codigo in codigos_existentes:
                st.error("Este codigo ja esta cadastrado.")
            else:
                novo = {
                    "codigo": codigo, "nome": nome, "tipo_base": novo_tipo,
                    "localidade": nova_localidade.strip(),
                    "residuo_puro": novo_residuo if novo_residuo is not None else 0.0,
                    "status": "Ativo",
                }
                st.session_state.catalogo_barros = pd.concat(
                    [st.session_state.catalogo_barros, pd.DataFrame([novo])], ignore_index=True,
                )
                if persistir_dados("barros"):
                    st.success("Barro cadastrado.")
                    st.rerun()

    with col_edicao:
        st.subheader("Editar ou excluir barro")

        codigos = st.session_state.catalogo_barros["codigo"].astype(str).tolist()

        if len(codigos) == 0:
            st.info("Nenhum barro cadastrado.")
        else:
            codigo_selecionado = st.selectbox("Selecione:", codigos, key="barro_selecionado")
            indice = st.session_state.catalogo_barros[
                st.session_state.catalogo_barros["codigo"].astype(str) == codigo_selecionado
            ].index[0]
            barro_atual = st.session_state.catalogo_barros.loc[indice]

            with st.form("form_editar_barro"):
                edit_codigo = st.text_input("Codigo:", value=texto_seguro(barro_atual["codigo"]))
                edit_nome = st.text_input("Nome:", value=texto_seguro(barro_atual["nome"]))

                tipos = ["Preto", "Amarelo", "Branco"]
                tipo_atual = texto_seguro(barro_atual["tipo_base"], "Preto")
                edit_tipo = st.selectbox("Tipo:", tipos, index=tipos.index(tipo_atual) if tipo_atual in tipos else 0)

                edit_localidade = st.text_input("Localidade:", value=texto_seguro(barro_atual["localidade"]))
                edit_residuo = st.number_input(
                    "Residuo puro (%)", min_value=0.0, max_value=100.0,
                    value=numero_seguro(barro_atual["residuo_puro"]), step=0.1,
                )

                status_opcoes = ["Ativo", "Inativo"]
                status_atual = texto_seguro(barro_atual["status"], "Ativo")
                edit_status = st.selectbox(
                    "Status:", status_opcoes, index=status_opcoes.index(status_atual) if status_atual in status_opcoes else 0,
                )
                salvar = st.form_submit_button("Salvar alteracoes", type="primary", use_container_width=True)

            if salvar:
                novo_codigo = edit_codigo.strip().upper()
                novo_nome = edit_nome.strip()
                codigo_duplicado = novo_codigo != codigo_selecionado and novo_codigo in codigos

                if not novo_codigo or not novo_nome:
                    st.error("Codigo e nome sao obrigatorios.")
                elif codigo_duplicado:
                    st.error("O novo codigo ja esta cadastrado.")
                else:
                    codigo_mudou = novo_codigo != codigo_selecionado

                    if codigo_mudou:
                        for coluna in ["cod_barro_preto", "cod_barro_amarelo", "cod_barro_branco"]:
                            st.session_state.df_master[coluna] = st.session_state.df_master[coluna].replace(
                                codigo_selecionado, novo_codigo,
                            )
                        st.session_state.analises_puro["codigo_barro"] = (
                            st.session_state.analises_puro["codigo_barro"].replace(codigo_selecionado, novo_codigo)
                        )

                    catalogo = st.session_state.catalogo_barros
                    catalogo.at[indice, "codigo"] = novo_codigo
                    catalogo.at[indice, "nome"] = novo_nome
                    catalogo.at[indice, "tipo_base"] = edit_tipo
                    catalogo.at[indice, "localidade"] = edit_localidade.strip()
                    catalogo.at[indice, "residuo_puro"] = edit_residuo
                    catalogo.at[indice, "status"] = edit_status

                    sucesso = persistir_dados("barros")
                    if codigo_mudou:
                        sucesso = persistir_dados("lotes") and sucesso
                        sucesso = persistir_dados("puro") and sucesso

                    if sucesso:
                        st.success("Barro atualizado.")
                        st.rerun()

            confirmar = st.checkbox(
                "Confirmo a exclusao definitiva deste barro", key=f"confirmar_exclusao_barro_{codigo_selecionado}",
            )
            if st.button("Excluir barro selecionado", key=f"excluir_barro_{codigo_selecionado}", use_container_width=True):
                if not confirmar:
                    st.error("Marque a confirmacao antes de excluir.")
                else:
                    lotes = st.session_state.df_master
                    usado_lotes = (
                        (lotes["cod_barro_preto"].astype(str) == codigo_selecionado).any()
                        or (lotes["cod_barro_amarelo"].astype(str) == codigo_selecionado).any()
                        or (lotes["cod_barro_branco"].astype(str) == codigo_selecionado).any()
                    )
                    usado_puro = (
                        st.session_state.analises_puro["codigo_barro"].astype(str) == codigo_selecionado
                    ).any()

                    if usado_lotes or usado_puro:
                        st.error(
                            "Este barro possui historico. Para preservar a rastreabilidade, marque-o como Inativo."
                        )
                    else:
                        st.session_state.catalogo_barros = st.session_state.catalogo_barros[
                            st.session_state.catalogo_barros["codigo"].astype(str) != codigo_selecionado
                        ].reset_index(drop=True)
                        if persistir_dados("barros"):
                            st.success("Barro excluido.")
                            st.rerun()

    st.divider()
    st.subheader("Barros cadastrados")
    st.dataframe(st.session_state.catalogo_barros, use_container_width=True, hide_index=True)


# ============================================================
# ABA 5 - CADASTRO DE PRODUTOS
# ============================================================

def renderizar_produtos():
    st.header("Cadastro e Controle de Produtos / Blocos")
    st.caption(
        f"O peso padrao de cada produto e a referencia para parede de {PAREDE_PADRAO_CM:.2f} cm "
        "e comprimento verde ideal."
    )

    col_novo, col_edicao = st.columns(2)

    with col_novo:
        st.subheader("Cadastrar novo produto")

        with st.form("form_novo_produto", clear_on_submit=True):
            novo_codigo = st.text_input("Codigo do produto:", value="")
            nova_descricao = st.text_input("Descricao:", value="")
            nova_largura = st.number_input("Largura (cm)", min_value=0.0, max_value=100.0, value=None, step=0.1)
            novo_nominal = st.number_input("Comprimento nominal (cm)", min_value=0.0, max_value=100.0, value=None, step=0.1)
            novo_verde = st.number_input("Comprimento verde ideal (cm)", min_value=0.0, max_value=100.0, value=None, step=0.1)
            novo_peso = st.number_input("Peso padrao (kg)", min_value=0.0, max_value=100.0, value=None, step=0.001, format="%.3f")
            cadastrar = st.form_submit_button("Cadastrar produto", type="primary", use_container_width=True)

        if cadastrar:
            codigo = novo_codigo.strip().upper()
            descricao = nova_descricao.strip()
            codigos_existentes = st.session_state.catalogo_produtos["codigo"].astype(str).tolist()

            if not codigo or not descricao:
                st.error("Informe o codigo e a descricao.")
            elif not campos_preenchidos(nova_largura, novo_nominal, novo_verde, novo_peso):
                st.error("Preencha todas as medidas e o peso.")
            elif nova_largura <= 0 or novo_nominal <= 0 or novo_verde <= 0 or novo_peso <= 0:
                st.error("As medidas e o peso precisam ser maiores que zero.")
            elif codigo in codigos_existentes:
                st.error("Este codigo ja esta cadastrado.")
            else:
                chave_comercial = (
                    f"{codigo} ({nova_largura:.1f}x{novo_nominal:.1f}x{novo_nominal:.1f} cm) - {descricao}"
                )
                novo = {
                    "chave_comercial": chave_comercial, "codigo": codigo, "largura": nova_largura,
                    "comprimento_nominal": novo_nominal, "comp_seco_ideal": novo_verde,
                    "peso_padrao": novo_peso, "status": "Ativo",
                }
                st.session_state.catalogo_produtos = pd.concat(
                    [st.session_state.catalogo_produtos, pd.DataFrame([novo])], ignore_index=True,
                )
                if persistir_dados("produtos"):
                    st.success("Produto cadastrado.")
                    st.rerun()

    with col_edicao:
        st.subheader("Editar ou excluir produto")

        codigos = st.session_state.catalogo_produtos["codigo"].astype(str).tolist()

        if len(codigos) == 0:
            st.info("Nenhum produto cadastrado.")
        else:
            codigo_selecionado = st.selectbox("Selecione:", codigos, key="produto_selecionado")
            indice = st.session_state.catalogo_produtos[
                st.session_state.catalogo_produtos["codigo"].astype(str) == codigo_selecionado
            ].index[0]
            produto_atual = st.session_state.catalogo_produtos.loc[indice]

            with st.form("form_editar_produto"):
                edit_codigo = st.text_input("Codigo:", value=texto_seguro(produto_atual["codigo"]))
                descricao_atual = texto_seguro(produto_atual["chave_comercial"]).split(" - ")[-1]
                edit_descricao = st.text_input("Descricao:", value=descricao_atual)
                edit_largura = st.number_input("Largura (cm)", min_value=0.0, value=numero_seguro(produto_atual["largura"]), step=0.1)
                edit_nominal = st.number_input("Comprimento nominal (cm)", min_value=0.0, value=numero_seguro(produto_atual["comprimento_nominal"]), step=0.1)
                edit_verde = st.number_input("Comprimento verde ideal (cm)", min_value=0.0, value=numero_seguro(produto_atual["comp_seco_ideal"]), step=0.1)
                edit_peso = st.number_input("Peso padrao (kg)", min_value=0.0, value=numero_seguro(produto_atual["peso_padrao"]), step=0.001, format="%.3f")

                status_opcoes = ["Ativo", "Inativo"]
                status_atual = texto_seguro(produto_atual["status"], "Ativo")
                edit_status = st.selectbox(
                    "Status:", status_opcoes, index=status_opcoes.index(status_atual) if status_atual in status_opcoes else 0,
                )
                salvar = st.form_submit_button("Salvar alteracoes", type="primary", use_container_width=True)

            if salvar:
                novo_codigo = edit_codigo.strip().upper()
                nova_descricao = edit_descricao.strip()
                codigo_duplicado = novo_codigo != codigo_selecionado and novo_codigo in codigos

                if not novo_codigo or not nova_descricao:
                    st.error("Codigo e descricao sao obrigatorios.")
                elif edit_largura <= 0 or edit_nominal <= 0 or edit_verde <= 0 or edit_peso <= 0:
                    st.error("As medidas e o peso precisam ser maiores que zero.")
                elif codigo_duplicado:
                    st.error("O novo codigo ja esta cadastrado.")
                else:
                    codigo_mudou = novo_codigo != codigo_selecionado
                    if codigo_mudou:
                        st.session_state.df_master["tipo_bloco"] = st.session_state.df_master["tipo_bloco"].replace(
                            codigo_selecionado, novo_codigo,
                        )

                    nova_chave = (
                        f"{novo_codigo} ({edit_largura:.1f}x{edit_nominal:.1f}x{edit_nominal:.1f} cm) - {nova_descricao}"
                    )
                    catalogo = st.session_state.catalogo_produtos
                    catalogo.at[indice, "codigo"] = novo_codigo
                    catalogo.at[indice, "chave_comercial"] = nova_chave
                    catalogo.at[indice, "largura"] = edit_largura
                    catalogo.at[indice, "comprimento_nominal"] = edit_nominal
                    catalogo.at[indice, "comp_seco_ideal"] = edit_verde
                    catalogo.at[indice, "peso_padrao"] = edit_peso
                    catalogo.at[indice, "status"] = edit_status

                    sucesso = persistir_dados("produtos")
                    if codigo_mudou:
                        sucesso = persistir_dados("lotes") and sucesso

                    if sucesso:
                        st.success("Produto atualizado.")
                        st.rerun()

            confirmar = st.checkbox(
                "Confirmo a exclusao definitiva deste produto", key=f"confirmar_exclusao_produto_{codigo_selecionado}",
            )
            if st.button("Excluir produto selecionado", key=f"excluir_produto_{codigo_selecionado}", use_container_width=True):
                if not confirmar:
                    st.error("Marque a confirmacao antes de excluir.")
                else:
                    produto_em_uso = (st.session_state.df_master["tipo_bloco"].astype(str) == codigo_selecionado).any()
                    if produto_em_uso:
                        st.error(
                            "Este produto possui historico. Para preservar a rastreabilidade, marque-o como Inativo."
                        )
                    else:
                        st.session_state.catalogo_produtos = st.session_state.catalogo_produtos[
                            st.session_state.catalogo_produtos["codigo"].astype(str) != codigo_selecionado
                        ].reset_index(drop=True)
                        if persistir_dados("produtos"):
                            st.success("Produto excluido.")
                            st.rerun()

    st.divider()
    st.subheader("Produtos cadastrados")
    st.dataframe(st.session_state.catalogo_produtos, use_container_width=True, hide_index=True)


# ============================================================
# ABAS DO SISTEMA
# ============================================================

(tab_diagnostico, tab_registro, tab_puro, tab_barros, tab_produtos) = st.tabs([
    "Diagnostico e Previsao",
    "Registrar Analise de Mistura",
    "Analise de Barro Puro",
    "Gerenciar Barros",
    "Gerenciar Produtos",
])

with tab_diagnostico:
    renderizar_diagnostico()

with tab_registro:
    renderizar_registro_lotes()

with tab_puro:
    renderizar_barro_puro()

with tab_barros:
    renderizar_barros()

with tab_produtos:
    renderizar_produtos()
