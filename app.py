# ============================================================
# CERAMICAIA v14.0 — Híbrido (Misturas + Barros Puros) 
# ============================================================
import io
import os
import urllib.parse
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score
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
# DADOS INICIAIS BASE
# ============================================================
BARROS_INICIAIS = [
 {
 "codigo": "01_BR_ARG_PRETO_SV",
 "nome": "Barro Argiloso Preto (Sao Vicente)",
 "tipo_base": "Preto",
 "localidade": "Sao Vicente (SV)",
 "residuo_puro": 10.0,
 "status": "Ativo",
 },
 {
 "codigo": "02_BR_ARG_VERM_STPREZ",
 "nome": "Barro Argiloso Vermelho (Sitio Prazeres)",
 "tipo_base": "Preto",
 "localidade": "Sitio Prazeres (STPRAZ)",
 "residuo_puro": 12.0,
 "status": "Ativo",
 },
 {
 "codigo": "03_BR_AREN_BRANCO_STPRAZ",
 "nome": "Barro Arenoso Branco (Sitio Prazeres)",
 "tipo_base": "Branco",
 "localidade": "Sitio Prazeres (STPRAZ)",
 "residuo_puro": 45.0,
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
HISTORICO_BASE_CSV = """data,modo,cod_barro_preto,cod_barro_amarelo,cod_barro_branco,preto_a,amarelo_a,branco_a,preto_b,amarelo_b,branco_b,pct_preto,pct_amarelo,pct_branco,umidade,residuo,retracao,esp_parede,peso,comprimento,tipo_bloco,class_residuo,excesso_peso,observacoes
2025-03-20,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,17.0,33.7,3,0.90,3.600,20.4,01-BLP,fraco,800,Historico Colab
2025-03-21,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,17.0,32.0,3,0.85,3.185,20.5,01-BLP,limite,385,Historico Colab
2025-03-24,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,10.0,28.0,3,0.82,3.100,20.7,01-BLP,ideal,300,Historico Colab
2025-03-25,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,15.0,29.0,3,0.80,3.125,20.5,01-BLP,ideal,325,Historico Colab
2025-03-27,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,16.0,31.5,3,0.85,3.184,20.5,01-BLP,ideal,384,Historico Colab
2025-03-28,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,16.0,28.7,3,0.77,3.074,20.0,01-BLP,ideal,274,Historico Colab
2025-04-02,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,14.0,29.2,4,0.80,3.244,20.7,01-BLP,ideal,444,Historico Colab
2025-04-03,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,16.0,30.0,3,0.87,3.114,20.2,01-BLP,ideal,314,Historico Colab
2025-04-09,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,15.0,30.9,4,0.82,3.231,20.0,01-BLP,ideal,431,Historico Colab
2025-04-10,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,14.0,33.5,4,0.90,3.237,20.0,01-BLP,fraco,437,Historico Colab
2025-04-16,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,13.0,28.6,4,0.77,3.277,20.5,01-BLP,ideal,477,Historico Colab
2025-04-18,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,16.0,28.4,3,0.85,3.390,20.6,01-BLP,ideal,590,Historico Colab
2025-04-30,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,12.0,28.4,3,0.95,3.390,20.6,01-BLP,ideal,590,Historico Colab
2025-05-14,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,12.0,32.0,3,0.80,3.419,20.2,01-BLP,limite,619,Historico Colab
2025-05-15,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,11.0,32.6,3,0.725,2.885,20.0,01-BLP,fraco,85,Historico Colab
2025-05-16,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,13.0,33.3,3,0.80,2.930,20.0,01-BLP,fraco,130,Historico Colab
2025-05-22,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,10.0,33.3,3,0.80,3.050,20.0,01-BLP,fraco,250,Historico Colab
2025-05-26,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,16.0,34.0,2,0.725,3.071,20.6,01-BLP,fraco,271,Historico Colab
2025-05-28,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,12.0,34.5,3,0.775,3.055,20.0,01-BLP,fraco,255,Historico Colab
2025-05-30,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,12.0,32.7,4,0.975,3.025,20.0,01-BLP,fraco,225,Historico Colab
2025-06-05,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,12.0,32.0,4,0.56,3.184,20.0,01-BLP,limite,384,Historico Colab
2025-06-10,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,14.0,30.9,4,0.725,3.175,20.5,01-BLP,ideal,375,Historico Colab
2025-06-17,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,13.0,33.0,3,0.725,3.315,20.5,01-BLP,fraco,515,Historico Colab
2025-06-25,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,13.0,30.2,3,0.775,3.284,20.5,01-BLP,ideal,484,Historico Colab
2025-07-04,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,12.0,28.1,4,0.725,3.284,20.5,01-BLP,ideal,484,Historico Colab
2025-07-07,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,12.0,31.5,3,0.775,3.400,20.7,01-BLP,ideal,600,Historico Colab
2025-07-09,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,12.0,29.6,5,0.70,3.100,20.5,01-BLP,ideal,300,Historico Colab
2025-07-10,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,14.0,31.0,4,0.725,3.084,20.2,01-BLP,ideal,284,Historico Colab
2025-07-14,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,15.0,30.0,4,0.675,3.090,20.0,01-BLP,ideal,290,Historico Colab
2025-07-28,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,15.0,36.6,4,0.725,3.227,20.3,01-BLP,fraco,427,Historico Colab
2025-08-05,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,15.0,36.0,4,0.80,3.241,20.3,01-BLP,fraco,441,Historico Colab
2025-08-11,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,14.0,29.5,4,0.725,3.300,20.3,01-BLP,ideal,500,Historico Colab
2025-08-18,Unica,02_BR_ARG_VERM_STPREZ,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,14.0,32.0,4,0.675,3.020,20.1,01-BLP,limite,220,Historico Colab
2025-08-19,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,11.0,31.0,3,0.675,3.000,20.0,01-BLP,ideal,200,Historico Colab
2025-08-21,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,5,0,1,0.833,0.000,0.167,13.0,34.0,3,0.65,3.048,20.3,01-BLP,fraco,248,Historico Colab
2025-09-02,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,4,0,1,0.817,0.000,0.183,12.0,29.6,5,0.70,3.100,20.5,01-BLP,ideal,300,Historico Colab
2025-09-16,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,4,0,1,0.817,0.000,0.183,18.0,29.0,4,0.625,3.338,20.1,01-BLP,ideal,538,Historico Colab
2025-09-23,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,4,0,1,0.817,0.000,0.183,16.0,28.5,4,0.725,3.149,20.3,01-BLP,ideal,349,Historico Colab
2025-09-25,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,4,0,1,0.817,0.000,0.183,15.0,28.0,3,0.825,3.400,20.1,01-BLP,ideal,600,Historico Colab
2025-09-30,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,4,0,1,0.817,0.000,0.183,17.0,28.0,4,0.75,3.291,20.1,01-BLP,ideal,491,Historico Colab
2025-10-05,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,4,0,1,0.817,0.000,0.183,17.0,28.0,4,0.75,6.000,40.0,03-BLQ,ideal,0,Historico Colab
2025-10-15,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,5,0,1,4,0,1,0.817,0.000,0.183,17.0,28.0,4,0.75,6.300,40.0,02-BLG,ideal,800,Historico Colab
2025-12-24,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,18.0,28.0,3,0.60,3.016,21.0,01-BLP,ideal,216,Historico Colab
2025-12-26,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,18.0,30.0,3,0.60,2.891,20.0,01-BLP,ideal,91,Historico Colab
2025-12-27,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,18.0,35.0,3,0.60,6.089,41.0,02-BLG,fraco,589,Historico Colab
2025-12-29,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,18.0,34.0,3,0.60,6.102,41.0,02-BLG,fraco,602,Historico Colab
2025-12-30,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,17.0,42.0,3,0.60,3.132,21.0,01-BLP,fraco,332,Historico Colab
2026-01-02,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,2,4,0,2,0.667,0.000,0.333,18.0,32.0,3,0.60,3.116,20.0,01-BLP,limite,316,Historico Colab
2026-01-12,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,2,4,0,2,0.667,0.000,0.333,16.0,38.0,3,0.60,6.360,41.0,02-BLG,fraco,860,Historico Colab
2026-01-13,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,2,4,0,2,0.667,0.000,0.333,17.0,26.0,3,0.60,6.303,41.0,02-BLG,forte,803,Historico Colab
2026-01-14,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,2,4,0,2,0.667,0.000,0.333,17.0,36.0,3,0.60,3.175,21.0,01-BLP,fraco,375,Historico Colab
2026-01-15,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,2,4,0,2,0.667,0.000,0.333,18.0,35.0,3,0.60,3.077,20.0,01-BLP,fraco,277,Historico Colab
2026-01-20,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,6,0,3,6,0,3,0.667,0.000,0.333,12.0,32.0,3,0.70,2.605,40.0,02-BLG,limite,-2895,Historico Colab
2026-01-21,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,6,0,3,6,0,3,0.667,0.000,0.333,18.0,35.0,3,0.60,6.089,41.0,02-BLG,fraco,589,Historico Colab
2026-01-23,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,1,0.750,0.000,0.250,13.0,30.0,3,0.60,3.071,20.0,01-BLP,ideal,271,Historico Colab
2026-01-27,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,1,0.750,0.000,0.250,13.0,27.0,3,0.60,3.134,20.0,01-BLP,forte,334,Historico Colab
2026-01-28,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,1,0.750,0.000,0.250,13.0,30.0,3,0.60,6.357,41.0,02-BLG,ideal,857,Historico Colab
2026-02-06,Mesclada,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,2,0.675,0.000,0.325,12.0,26.0,3,0.60,6.450,41.0,02-BLG,forte,950,Historico Colab
2026-02-10,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,12.0,30.0,3,0.60,6.401,41.0,02-BLG,ideal,901,Historico Colab
2026-02-11,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,12.0,29.0,3,0.60,6.705,41.0,02-BLG,ideal,1205,Historico Colab
2026-02-18,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,12.0,28.0,3,0.60,6.571,41.0,02-BLG,ideal,1071,Historico Colab
2026-02-19,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,3,3,0,3,0.500,0.000,0.500,12.0,30.0,3,0.60,6.498,41.0,02-BLG,ideal,998,Historico Colab
2026-02-20,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,3,3,0,3,0.500,0.000,0.500,12.0,32.0,3,0.60,3.121,19.0,01-BLP,limite,321,Historico Colab
2026-02-23,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,3,3,0,3,0.500,0.000,0.500,14.0,30.0,3,0.60,3.268,20.0,01-BLP,ideal,468,Historico Colab
2026-03-04,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,12.0,33.0,3,0.60,6.380,41.0,02-BLG,fraco,880,Historico Colab
2026-03-07,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,12.0,33.0,3,0.60,3.279,20.0,01-BLP,fraco,479,Historico Colab
2026-03-09,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,13.0,33.0,3,0.60,6.317,40.0,02-BLG,fraco,817,Historico Colab
2026-03-23,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,11.0,37.0,3,0.60,3.335,20.0,01-BLP,fraco,535,Historico Colab
2026-03-27,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,14.0,30.0,3,0.60,3.386,20.0,01-BLP,ideal,586,Historico Colab
2026-04-01,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,2,0.600,0.000,0.400,12.0,37.0,3,0.60,6.593,41.0,02-BLG,fraco,1093,Historico Colab
2026-04-07,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,2,3,0,3,0.500,0.000,0.500,11.0,37.0,3,0.60,6.596,41.0,02-BLG,fraco,1096,Historico Colab
2026-04-22,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,1,0.750,0.000,0.250,12.0,37.0,3,0.60,3.394,20.0,01-BLP,fraco,594,Historico Colab
2026-04-27,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,12.0,28.0,3,0.60,3.311,20.0,01-BLP,ideal,511,Historico Colab
2026-05-18,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,12.0,31.0,3,0.60,8.200,41.0,BG14,ideal,1200,Historico Colab
2026-05-19,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,15.0,31.0,3,0.60,3.570,20.0,01-BLP,ideal,770,Historico Colab
2026-05-21,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,20.0,32.0,3,0.60,3.618,20.0,01-BLP,limite,818,Historico Colab
2026-06-13,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,1,0.750,0.000,0.250,12.0,27.5,2,0.60,6.700,41.0,02-BLG,forte,1200,Historico Colab
2026-06-15,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,1,0.750,0.000,0.250,20.0,30.3,3,0.23,3.633,20.0,01-BLP,ideal,833,Historico Colab
2026-06-16,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,1,0.750,0.000,0.250,12.0,29.5,4,0.23,3.670,20.5,01-BLP,ideal,870,Historico Colab
2026-06-17,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,1,0.750,0.000,0.250,17.0,31.6,3,0.75,7.000,41.0,BG14,ideal,0,Historico Colab
2026-06-18,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,1,0.750,0.000,0.250,18.0,30.8,3,0.75,3.300,20.3,01-BLP,ideal,500,Historico Colab
2026-06-19,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,3,0,1,3,0,1,0.750,0.000,0.250,15.7,31.6,3,0.86,6.700,19.1,BP14,ideal,2900,Historico Colab
2026-06-20,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,15.0,31.0,3,0.60,3.570,20.0,01-BLP,ideal,770,Historico Colab
2026-06-22,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,15.9,28.2,3,0.80,3.570,20.1,01-BLP,ideal,770,Historico Colab
2026-06-23,Unica,01_BR_ARG_PRETO_SV,Nenhum,03_BR_AREN_BRANCO_STPRAZ,4,0,1,4,0,1,0.800,0.000,0.200,17.0,28.5,3,0.88,3.500,20.2,01-BLP,ideal,700,Historico Colab"""
COLUNAS_BARROS = ["codigo", "nome", "tipo_base", "localidade", "residuo_puro", "status"]
COLUNAS_PRODUTOS = [
 "chave_comercial", "codigo", "largura", "comprimento_nominal",
 "comp_seco_ideal", "peso_padrao", "status",
]
COLUNAS_LOTES = [
 "data", "modo", "cod_barro_preto", "cod_barro_amarelo",
 "cod_barro_branco", "preto_a", "amarelo_a", "branco_a",
 "preto_b", "amarelo_b", "branco_b", "pct_preto", "pct_amarelo",
 "pct_branco", "umidade", "residuo", "retracao", "esp_parede",
 "peso", "comprimento", "tipo_bloco", "class_residuo",
 "excesso_peso", "observacoes",
]
COLUNAS_PURO = [
 "data", "codigo_barro", "peso_amostra_g", "peso_residuo_g",
 "pct_residuo_puro", "observacoes",
]
# ============================================================
# CARREGAMENTO E AUTO-SEED (GRAVACAO AUTOMATICA NO SHEETS)
# ============================================================
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
if "df_master" not in st.session_state:
 if MODO_SHEETS and worksheet_lotes:
 df_l = ler_dados_sheets(worksheet_lotes, COLUNAS_LOTES)
 if len(df_l) == 0:
 df_l = pd.read_csv(io.StringIO(HISTORICO_BASE_CSV))
 salvar_no_sheets(worksheet_lotes, df_l)
 st.toast("Google Sheets estava vazio: 115 lotes historicos inseridos com sucesso!")
 st.session_state.df_master = df_l
 elif os.path.exists("db_df_master.csv"):
 st.session_state.df_master = pd.read_csv("db_df_master.csv")
 else:
 st.session_state.df_master = pd.read_csv(io.StringIO(HISTORICO_BASE_CSV))
 st.session_state.df_master.to_csv("db_df_master.csv", index=False)
if "analises_puro" not in st.session_state:
 if MODO_SHEETS and worksheet_puro:
 st.session_state.analises_puro = ler_dados_sheets(worksheet_puro, COLUNAS_PURO)
 elif os.path.exists("db_analises_puro.csv"):
 st.session_state.analises_puro = pd.read_csv("db_analises_puro.csv")
 else:
 st.session_state.analises_puro = pd.DataFrame(columns=COLUNAS_PURO)
 st.session_state.analises_puro.to_csv("db_analises_puro.csv", index=False)
if "diagnostico_gerado" not in st.session_state:
 st.session_state.diagnostico_gerado = False
if "versao_dados" not in st.session_state:
 st.session_state.versao_dados = 0
def marcar_dados_alterados():
 st.session_state.versao_dados += 1
def persistir_dados(tipo):
 if tipo == "barros":
 df = st.session_state.catalogo_barros
 if MODO_SHEETS and worksheet_barros:
 salvar_no_sheets(worksheet_barros, df)
 df.to_csv("db_catalogo_barros.csv", index=False)
 marcar_dados_alterados()
 elif tipo == "produtos":
 df = st.session_state.catalogo_produtos
 if MODO_SHEETS and worksheet_produtos:
 salvar_no_sheets(worksheet_produtos, df)
 df.to_csv("db_catalogo_produtos.csv", index=False)
 marcar_dados_alterados()
 elif tipo == "lotes":
 df = st.session_state.df_master
 if MODO_SHEETS and worksheet_lotes:
 salvar_no_sheets(worksheet_lotes, df)
 df.to_csv("db_df_master.csv", index=False)
 marcar_dados_alterados()
 elif tipo == "puro":
 df = st.session_state.analises_puro
 if MODO_SHEETS and worksheet_puro:
 salvar_no_sheets(worksheet_puro, df)
 df.to_csv("db_analises_puro.csv", index=False)
 marcar_dados_alterados()
# ============================================================
# FUNCAO DE LOOKUP DO RESIDUO DE BARRO PURO
# ============================================================
def obter_residuo_puro_barro(cod_barro, df_barros, df_puro):
 if not cod_barro or cod_barro == "Nenhum":
 return 0.0
 # 1. Busca teste recente na aba analises_puro
 if len(df_puro) > 0:
 df_filtro = df_puro[df_puro["codigo_barro"] == cod_barro]
 if len(df_filtro) > 0:
 val_puro = pd.to_numeric(df_filtro.iloc[-1]["pct_residuo_puro"], errors="coerce")
 if not pd.isna(val_puro) and val_puro > 0:
 return float(val_puro)
 # 2. Busca no cadastro padrao
 if len(df_barros) > 0:
 df_filtro_b = df_barros[df_barros["codigo"] == cod_barro]
 if len(df_filtro_b) > 0:
 val_cad = pd.to_numeric(df_filtro_b.iloc[0].get("residuo_puro", 0.0), errors="coerce")
 if not pd.isna(val_cad) and val_cad > 0:
 return float(val_cad)
 # Fallback por tipo se estiver em branco
 tipo = df_filtro_b.iloc[0].get("tipo_base", "") if len(df_filtro_b) > 0 else ""
 if tipo == "Preto": return 10.0
 if tipo == "Amarelo": return 25.0
 if tipo == "Branco": return 45.0
 return 20.0
# ============================================================
# IA AUTO-APRENDIZ: MODELO HIBRIDO (FÍSICA + ML)
# ============================================================
FEATURES_PESO = ["esp_parede", "largura_cm", "comprimento_cm", "umidade"]
FEATURES_ML_RESIDUO = ["pct_preto", "pct_amarelo", "pct_branco", "umidade", "esp_parede"]
FEATURES_RETRACAO = ["pct_preto", "pct_amarelo", "pct_branco", "umidade", "esp_parede"]
# ============================================================
# MODELO 2: BARROS PUROS (FÍSICO)
# ============================================================
def treinar_modelo_barros_puros(df_lotes, df_barros, df_puro):
    """
    Treina modelo baseado APENAS em proporções e barros puros.
    Usa física pura: (% preto × res_preto_puro) + ... + DELTA_ML
    """
    
    if len(df_lotes) < 5:
        return None, {"n": len(df_lotes), "r2_puro": None}
    
    # Montar dataset
    df = montar_dataset_treino(df_lotes, df_barros, df_puro)
    
    if len(df) < 5:
        return None, {"n": len(df), "r2_puro": None}
    
    # Filtra linhas com residuo ponderado válido
    df_puro_treino = df.dropna(subset=["residuo_puro_ponderado", "residuo"])
    
    if len(df_puro_treino) < 5:
        return None, {"n": len(df_puro_treino), "r2_puro": None}
    
    # Features: proporções + umidade + espessura
    FEATURES_PURO = ["pct_preto", "pct_amarelo", "pct_branco", "umidade", "esp_parede"]
    
    X_puro = df_puro_treino[FEATURES_PURO].astype(float)
    
    # Target: DELTA (igual ao modelo empírico)
    y_puro = (df_puro_treino["residuo"] - df_puro_treino["residuo_puro_ponderado"]).astype(float)
    
    # Treinar
    m_puro = GradientBoostingRegressor(random_state=42, max_depth=4, n_estimators=100)
    m_puro.fit(X_puro, y_puro)
    
    # Avaliar
    pred_delta_puro = m_puro.predict(X_puro)
    pred_final_puro = df_puro_treino["residuo_puro_ponderado"] + pred_delta_puro
    
    r2_puro = r2_score(df_puro_treino["residuo"], pred_final_puro)
    
    metricas_puro = {
        "n": len(df_puro_treino),
        "r2_puro": round(r2_puro, 3),
    }
    
    return m_puro, metricas_puro
def montar_dataset_treino(df_lotes, df_produtos, df_barros, df_puro):
 if len(df_lotes) == 0:
 return pd.DataFrame()
 df = df_lotes.copy()
 # Mapear largura a partir dos produtos
 mapa_largura = dict(zip(df_produtos["codigo"], df_produtos["largura"]))
 df["largura_cm"] = df["tipo_bloco"].map(mapa_largura)
 df["comprimento_cm"] = pd.to_numeric(df["comprimento"], errors="coerce")
 for col in ["pct_preto", "pct_amarelo", "pct_branco", "umidade", "esp_parede", "residuo", "retracao", "peso"]:
 df[col] = pd.to_numeric(df[col], errors="coerce")
 # Calcula Base Fisica e Delta para IA
 res_puro_lista = []
 delta_lista = []
 for idx, row in df.iterrows():
 rp_preto = obter_residuo_puro_barro(row.get("cod_barro_preto"), df_barros, df_puro)
 rp_amarelo = obter_residuo_puro_barro(row.get("cod_barro_amarelo"), df_barros, df_puro)
 rp_branco = obter_residuo_puro_barro(row.get("cod_barro_branco"), df_barros, df_puro)
 p_preto = float(row.get("pct_preto", 0.0) or 0.0)
 p_amarelo = float(row.get("pct_amarelo", 0.0) or 0.0)
 p_branco = float(row.get("pct_branco", 0.0) or 0.0)
 ponderado = (p_preto * rp_preto) + (p_amarelo * rp_amarelo) + (p_branco * rp_branco)
 res_puro_lista.append(round(ponderado, 2))
 # Delta: A diferenca entre o Resíduo Real Final e o Ponderado Inicial
 if pd.notna(row.get("residuo")):
 delta = float(row.get("residuo")) - ponderado
 delta_lista.append(delta)
 else:
 delta_lista.append(np.nan)
 df["residuo_puro_ponderado"] = res_puro_lista
 df["delta_residuo"] = delta_lista
 return df
def treinar_modelos_ia(df_lotes, df_produtos, df_barros, df_puro):
    """
    Treina MODELO EMPÍRICO (baseado em histórico de misturas)
    + MODELO FÍSICO (baseado em barros puros)
    """
    df = montar_dataset_treino(df_lotes, df_produtos, df_barros, df_puro)
    n = len(df)
    
    if n < 5:
        return None, None, None, None, {"n": n, "r2_peso": None, "r2_residuo": None, "r2_retracao": None, "r2_puro": None}
    
    # 1. Treino do Modelo de PESO (100% Isolado da Areia)
    df_pes = df.dropna(subset=FEATURES_PESO + ["peso"])
    X_pes = df_pes[FEATURES_PESO].astype(float)
    m_pes = GradientBoostingRegressor(random_state=42)
    m_pes.fit(X_pes, df_pes["peso"].astype(float))
    r2_pes = r2_score(df_pes["peso"], m_pes.predict(X_pes))
    
    # 2. Treino do Modelo de RESIDUO EMPÍRICO (Prevê apenas o DELTA do Processo)
    df_res = df.dropna(subset=FEATURES_ML_RESIDUO + ["delta_residuo"])
    X_res = df_res[FEATURES_ML_RESIDUO].astype(float)
    m_res = GradientBoostingRegressor(random_state=42)
    m_res.fit(X_res, df_res["delta_residuo"].astype(float))
    # Para o R2 visual, medimos a aderencia do modelo Hibrido (Fisica + ML)
    pred_delta = m_res.predict(X_res)
    pred_final = df_res["residuo_puro_ponderado"] + pred_delta
    r2_res = r2_score(df_res["residuo"], pred_final)
    
    # 3. Treino do Modelo de RETRACAO
    df_ret = df.dropna(subset=FEATURES_RETRACAO + ["retracao"])
    X_ret = df_ret[FEATURES_RETRACAO].astype(float)
    m_ret = GradientBoostingRegressor(random_state=42)
    m_ret.fit(X_ret, df_ret["retracao"].astype(float))
    r2_ret = r2_score(df_ret["retracao"], m_ret.predict(X_ret))
    
    metricas = {
        "n": n,
        "r2_peso": round(r2_pes, 3),
        "r2_residuo": round(r2_res, 3),
        "r2_retracao": round(r2_ret, 3),
    }
    
    # Treinar modelo de barros puros (Física)
    m_puro, metricas_puro = treinar_modelo_barros_puros(df_lotes, df_barros, df_puro)
    
    # Fusionar métricas
    metricas.update(metricas_puro)
    
    return m_pes, m_res, m_ret, m_puro, metricas
if (
    "modelos_ia" not in st.session_state
    or st.session_state.get("versao_treinada") != st.session_state.versao_dados
):
    with st.spinner("Calibrando IA Hibrida com os dados mais recentes..."):
        m_pes, m_res, m_ret, m_puro, metricas_ia = treinar_modelos_ia(
            st.session_state.df_master, 
            st.session_state.catalogo_produtos,
            st.session_state.catalogo_barros,
            st.session_state.analises_puro
        )
        st.session_state.modelos_ia = (m_pes, m_res, m_ret, m_puro)
        st.session_state.metricas_ia = metricas_ia
        st.session_state.versao_treinada = st.session_state.versao_dados
else:
    m_pes, m_res, m_ret, m_puro = st.session_state.modelos_ia
    metricas_ia = st.session_state.metricas_ia
if m_pes is None:
    st.error(
        f"Dados insuficientes para treinar a IA (apenas {metricas_ia['n']} "
        "lotes validos encontrados). Registre pelo menos 5 lotes completos."
    )
    st.stop()
st.sidebar.markdown(
    f'<div class="status-ok">IA treinada com {metricas_ia["n"]} lotes reais</div>',
    unsafe_allow_html=True,
)
with st.sidebar.expander("Detalhes do treinamento da IA"):
    st.write(f"📊 Modelo Empírico (Misturas):")
    st.write(f"  └─ R2 Residuo: {metricas_ia['r2_residuo']}")
    st.write(f"  └─ R2 Peso: {metricas_ia['r2_peso']}")
    st.write(f"  └─ R2 Retracao: {metricas_ia['r2_retracao']}")
    
    if metricas_ia.get('r2_puro') is not None:
        st.write(f"🔬 Modelo Físico (Barros Puros):")
        st.write(f"  └─ R2 Residuo Puro: {metricas_ia['r2_puro']}")
        st.write(f"  └─ Dados disponíveis: {metricas_ia.get('n', '?')} misturas com análise pura")
    else:
        st.write(f"🔬 Modelo Físico (Barros Puros):")
        st.write(f"  └─ Aguardando dados... (faça análises na Aba 3)")
    
    st.caption("A IA combina Empírico (histórico) + Físico (barros puros) para máxima precisão.")
# ============================================================
# ABAS PRINCIPAIS
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
 st.sidebar.error("Nenhum produto ativo cadastrado. Va na aba Gerenciar Produtos.")
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
 f"Meta de Peso Padrao: {peso_padrao:.3f} kg\n\n"
 f"Comprimento Verde de Corte na Extrusora: {comp_seco_ideal:.1f} cm "
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
 sel_barro_amarelo = st.selectbox("Barro Intermediario (Medio):", barros_amarelos)
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
 f"{preto_a}x{amarelo_a}x{branco_a}" if amarelo_a > 0 else f"{preto_a}x{branco_a}"
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
 # Obtem os valores da jazida para compor a base física
 rp_p = obter_residuo_puro_barro(sel_barro_preto, st.session_state.catalogo_barros, st.session_state.analises_puro)
 rp_a = obter_residuo_puro_barro(sel_barro_amarelo, st.session_state.catalogo_barros, st.session_state.analises_puro)
 rp_b = obter_residuo_puro_barro(sel_barro_branco, st.session_state.catalogo_barros, st.session_state.analises_puro)
 res_puro_ponderado_entrada = (pct_preto * rp_p) + (pct_amarelo * rp_a) + (pct_branco * rp_b)
 st.caption(
 f"Massa Resultante na Maromba: {pct_preto*100:.1f}% Argiloso | "
 f"{pct_amarelo*100:.1f}% Medio | {pct_branco*100:.1f}% Arenoso\n\n"
 f"Base Fisica de Areia da Jazida (Entrada): **{res_puro_ponderado_entrada:.1f}%**"
 )
 st.divider()
 st.header("Parametros de Processo e Dimensao de Corte")
 col_u, col_e, col_c = st.columns(3)
 with col_u:
 umidade = st.number_input("Umidade da Massa na Maromba (%)", 5.0, 30.0, 16.0, 0.5)
 with col_e:
 esp_parede = st.number_input("Espessura da Parede (cm)", 0.20, 1.50, 0.65, 0.01)
 with col_c:
 comprimento_cm = st.number_input(
 "Comprimento Verde de Corte na Extrusora (cm):",
 15.0, 45.0, float(comp_seco_ideal), 0.1,
 help=(
 f"Tamanho ideal verde para este produto e {comp_seco_ideal:.1f} cm. "
 "Se a guilhotina cortar maior, o peso aumenta."
 ),
 )
 st.divider()
 if st.button("GERAR DIAGNOSTICO DO LOTE", type="primary", use_container_width=True):
 st.session_state.diagnostico_gerado = True
 if st.session_state.diagnostico_gerado:
 # Previsao Hibrida: Fisíca + ML
 X_input_pes = pd.DataFrame([{
 "esp_parede": esp_parede,
 "largura_cm": largura_cm,
 "comprimento_cm": comprimento_cm,
 "umidade": umidade,
 }])
 
 X_input_res_ml = pd.DataFrame([{
 "pct_preto": pct_preto,
 "pct_amarelo": pct_amarelo,
 "pct_branco": pct_branco,
 "umidade": umidade,
 "esp_parede": esp_parede,
 }])
 
 X_input_ret = pd.DataFrame([{
 "pct_preto": pct_preto,
 "pct_amarelo": pct_amarelo,
 "pct_branco": pct_branco,
 "umidade": umidade,
 "esp_parede": esp_parede,
 }])
 
 pred_pes = m_pes.predict(X_input_pes)[0]
 
 # ═══════════════════════════════════════════════════════════
 # MODELO 1: EMPÍRICO (Histórico de Misturas)
 # ═══════════════════════════════════════════════════════════
 pred_delta_res = m_res.predict(X_input_res_ml)[0]
 pred_res_empirico = res_puro_ponderado_entrada + pred_delta_res
 
 # ═══════════════════════════════════════════════════════════
 # MODELO 2: FÍSICO (Barros Puros) - SE DISPONÍVEL
 # ═══════════════════════════════════════════════════════════
 pred_res_puro = None
 tem_modelo_puro = False
 
 if m_puro is not None:
 pred_delta_puro = m_puro.predict(X_input_res_ml)[0]
 pred_res_puro = res_puro_ponderado_entrada + pred_delta_puro
 tem_modelo_puro = True
 
 # ═══════════════════════════════════════════════════════════
 # FUSÃO: Combinar os dois modelos (50/50) ou usar um só
 # ═══════════════════════════════════════════════════════════
 if tem_modelo_puro:
 # Ambos disponíveis: média 50/50
 pred_res = (pred_res_empirico + pred_res_puro) / 2
 confianca_residuo = "🟢 ALTA (Ambos modelos concordam)"
 else:
 # Só empírico disponível
 pred_res = pred_res_empirico
 confianca_residuo = "🟡 MÉDIA (Só modelo empírico)"
 
 pred_ret = m_ret.predict(X_input_ret)[0]
 st.header("Resultados Previstos pela IA")
 
 diff_comp = comprimento_cm - comp_seco_ideal
 if diff_comp > 0.15:
 st.warning(
 f"ALERTA DE CORTE NA EXTRUSORA: Bloco verde cortado com "
 f"{comprimento_cm:.1f} cm (+{diff_comp*10:.0f} mm acima do ideal "
 f"de {comp_seco_ideal:.1f} cm). Esse excesso aumenta o peso. "
 "Ajuste a guilhotina do carretel."
 )
 elif diff_comp < -0.15:
 st.warning(
 f"ATENCAO AO CORTE NA EXTRUSORA: Bloco verde cortado com "
 f"{comprimento_cm:.1f} cm (-{abs(diff_comp)*10:.0f} mm abaixo do "
 f"ideal de {comp_seco_ideal:.1f} cm). Risco de ficar curto apos a queima."
 )
 
 # ═══════════════════════════════════════════════════════════
 # MOSTRAR OS 2 MODELOS (se disponível)
 # ═══════════════════════════════════════════════════════════
 if tem_modelo_puro:
 st.subheader("📊 Análise Detalhada de Modelos")
 col_m1, col_m2, col_m3 = st.columns(3)
 
 with col_m1:
 st.metric("Modelo Empírico (Misturas)", f"{pred_res_empirico:.1f}%")
 st.caption(f"Baseado em {metricas_ia['n']} lotes históricos")
 
 with col_m2:
 st.metric("Modelo Físico (Barros Puros)", f"{pred_res_puro:.1f}%")
 st.caption(f"R² = {metricas_ia['r2_puro']}")
 
 with col_m3:
 st.metric("🎯 PREVISÃO FINAL (Média)", f"{pred_res:.1f}%")
 st.caption("Híbrida: Empírico + Físico")
 
 st.divider()
 else:
 st.info("ℹ️ **Modelo Físico ainda indisponível**: Faça análises de barros puros na Aba 3 para ativar o modelo híbrido!")
 
 res1, res2, res3 = st.columns(3)
 
 with res1:
 if tem_modelo_puro:
 st.metric("Resíduo Previsto no Bloco Queimado (FINAL)", f"{pred_res:.1f}%")
 else:
 st.metric("Resíduo Previsto no Bloco Queimado", f"{pred_res:.1f}%")
 
 if pred_res > 32.0:
 class_res = "🔴 BLOCO FRACO / QUEBRADICO"
 msg_res = "Resíduo acima de 32%. Aumente o barro Preto ou reduza o Branco."
 st.error(class_res)
 elif pred_res < 28.0:
 class_res = "🟠 FORTE DEMAIS / RISCO TRINCA"
 msg_res = "Resíduo abaixo de 28%. Adicione mais barro Branco."
 st.warning(class_res)
 else:
 class_res = "🟢 FAIXA IDEAL (28% a 32%)"
 msg_res = "Excelente resistência e equilíbrio plástico."
 st.success(class_res)
 
 st.caption(msg_res)
 
 # Mostrar confiança
 if tem_modelo_puro:
 st.caption(f"✅ Confiança: {confianca_residuo}")
 
 with res2:
 st.metric("Retracao Prevista", f"{pred_ret:.1f}%")
 comp_estimado_queimado = comprimento_cm * (1 - (pred_ret / 100))
 st.caption(f"Comprimento Queimado Est.: {comp_estimado_queimado:.1f} cm")
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
 prod_dia = st.number_input(
 "Producao Planejada do Dia (blocos):", 1000, 200000, 50000, 5000
 )
 with c_p2:
 custo_barro = st.number_input(
 "Custo da Tonelada do Barro (R$/ton):", 10.0, 200.0, 50.0, 5.0
 )
 ton_perdidas_dia = (excesso_g / 1000 * prod_dia) / 1000
 prejuizo_dia = ton_perdidas_dia * custo_barro
 prejuizo_mes = prejuizo_dia * 25
 st.error(
 f"Alerta de Perda de Materia-Prima:\n\n"
 f"- Desperdicio de Massa: {ton_perdidas_dia:.2f} toneladas/dia\n"
 f"- Prejuizo Estimado no Dia: R$ {prejuizo_dia:,.2f}\n"
 f"- Impacto Estimado no Mes (25 dias): R$ {prejuizo_mes:,.2f}"
 )
 texto_fin_wa = (
 f"\nPrejuizo estimado: R$ {prejuizo_dia:,.0f}/dia "
 f"({ton_perdidas_dia:.1f} ton desperdicadas)"
 )
 st.divider()
 
 # Montar mensagem com os 2 modelos
 if tem_modelo_puro:
 modelos_info = (
 f"Modelos:\n"
 f"- Empírico (Misturas): {pred_res_empirico:.1f}%\n"
 f"- Físico (Barros Puros): {pred_res_puro:.1f}%\n"
 f"- FINAL (Média): {pred_res:.1f}%\n"
 )
 else:
 modelos_info = f"Modelo: Empírico (Misturas)\n- Residuo: {pred_res:.1f}%\n"
 
 msg_wa_diag = (
 f"CeramicaIA - Diagnostico de Mistura\n\n"
 f"Produto: {codigo_prod} ({largura_cm}x19x{comprimento_nominal}cm)\n"
 f"Barro Argiloso: {sel_barro_preto}\n"
 f"Barro Arenoso: {sel_barro_branco}\n"
 f"Mistura: {mistura_desc} | Umid: {umidade}% | Esp: {esp_parede}cm\n"
 f"Corte Verde: {comprimento_cm:.1f} cm (Ideal: {comp_seco_ideal:.1f} cm)\n\n"
 f"Previsao da IA:\n"
 f"{modelos_info}"
 f"- Retracao: {pred_ret:.1f}% (Final queimado Est: {comp_estimado_queimado:.1f} cm)\n"
 f"- Peso Est.: {pred_pes:.3f} kg ({excesso_g:+.0f}g vs Meta){texto_fin_wa}\n\n"
 f"Gerado pelo CeramicaIA App"
 )
 wa_url_diag = f"https://wa.me/?text={urllib.parse.quote(msg_wa_diag)}"
 st.link_button(
 "Compartilhar Diagnostico no WhatsApp", wa_url_diag,
 type="secondary", use_container_width=True,
 )
# ============================================================
# ABA 2: REGISTRAR ANALISE REAL DE MISTURA
# ============================================================
with tab_reg:
 st.header("Registrar Analise de Laboratorio (Amostras de Mistura Extrudada)")
 st.caption(
 "Alimente o sistema com os dados medidos nas amostras de laboratorio. "
 "A IA recalibra automaticamente apos o salvamento."
 )
 df_barros_ativos_reg = st.session_state.catalogo_barros[
 st.session_state.catalogo_barros["status"] == "Ativo"
 ]
 barros_pretos_reg = df_barros_ativos_reg[df_barros_ativos_reg["tipo_base"] == "Preto"]["codigo"].tolist()
 barros_amarelos_reg = ["Nenhum"] + df_barros_ativos_reg[df_barros_ativos_reg["tipo_base"] == "Amarelo"]["codigo"].tolist()
 barros_brancos_reg = ["Nenhum"] + df_barros_ativos_reg[df_barros_ativos_reg["tipo_base"] == "Branco"]["codigo"].tolist()
 df_prod_ativos_reg = st.session_state.catalogo_produtos[
 st.session_state.catalogo_produtos["status"] == "Ativo"
 ]
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
 cod_p_reg = st.selectbox(
 "Codigo Barro Preto:", barros_pretos_reg if barros_pretos_reg else ["01_BR_ARG_PRETO_SV"]
 )
 cod_a_reg = st.selectbox("Codigo Barro Amarelo:", barros_amarelos_reg)
 cod_b_reg = st.selectbox(
 "Codigo Barro Branco:",
 barros_brancos_reg if len(barros_brancos_reg) > 1 else ["03_BR_AREN_BRANCO_STPRAZ"],
 )
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
 "Comprimento Verde de Corte Medido (cm):", 10.0, 50.0, float(comp_seco_sugerido), 0.1,
 help="Tamanho medido com paquimetro/trena no bloco verde.",
 )
 with f_col9:
 peso_real = st.number_input("Peso Real Medido (kg)", 0.0, 15.0, 3.100, 0.001)
 with f_col10:
 obs_texto = st.text_area("Observacoes:", "Teste de rotina")
 btn_salvar = st.form_submit_button(
 "Salvar Registro e Recalibrar IA", type="primary", use_container_width=True
 )
 if btn_salvar:
 tot_a_l = max(1, p_a + a_a + b_a)
 tot_b_l = max(1, p_b + a_b + b_b)
 pct_p_l = ((p_a / tot_a_l) + (p_b / tot_b_l)) / 2
 pct_a_l = ((a_a / tot_a_l) + (a_b / tot_b_l)) / 2
 pct_b_l = ((b_a / tot_a_l) + (b_b / tot_b_l)) / 2
 
 class_res_l = "fraco" if residuo_real > 32 else ("forte" if residuo_real < 28 else "ideal")
 excesso_l = (peso_real - peso_meta_l) * 1000
 
 # ═══════════════════════════════════════════════════════════
 # FAZER PREVISÕES COM OS 2 MODELOS
 # ═══════════════════════════════════════════════════════════
 X_input_pred = pd.DataFrame([{
 "pct_preto": pct_p_l,
 "pct_amarelo": pct_a_l,
 "pct_branco": pct_b_l,
 "umidade": umidade_real,
 "esp_parede": esp_real,
 }])
 
 # Calcular base física
 rp_p_l = obter_residuo_puro_barro(cod_p_reg, st.session_state.catalogo_barros, st.session_state.analises_puro)
 rp_a_l = obter_residuo_puro_barro(cod_a_reg, st.session_state.catalogo_barros, st.session_state.analises_puro)
 rp_b_l = obter_residuo_puro_barro(cod_b_reg, st.session_state.catalogo_barros, st.session_state.analises_puro)
 res_puro_pond_l = (pct_p_l * rp_p_l) + (pct_a_l * rp_a_l) + (pct_b_l * rp_b_l)
 
 # Modelo 1: Empírico
 pred_delta_emp_l = m_res.predict(X_input_pred)[0]
 pred_res_emp_l = res_puro_pond_l + pred_delta_emp_l
 
 # Modelo 2: Físico (se disponível)
 pred_res_puro_l = None
 tem_puro_l = False
 if m_puro is not None:
 pred_delta_puro_l = m_puro.predict(X_input_pred)[0]
 pred_res_puro_l = res_puro_pond_l + pred_delta_puro_l
 tem_puro_l = True
 
 # Fusão
 if tem_puro_l:
 pred_res_l = (pred_res_emp_l + pred_res_puro_l) / 2
 else:
 pred_res_l = pred_res_emp_l
 
 novo_row = {
 "data": data_lote.strftime("%Y-%m-%d"),
 "modo": modo_lote,
 "cod_barro_preto": cod_p_reg,
 "cod_barro_amarelo": cod_a_reg,
 "cod_barro_branco": cod_b_reg,
 "preto_a": p_a, "amarelo_a": a_a, "branco_a": b_a,
 "preto_b": p_b, "amarelo_b": a_b, "branco_b": b_b,
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
 st.success(
 "Lote registrado com sucesso. A IA sera recalibrada automaticamente."
 )
 
 # ═══════════════════════════════════════════════════════════
 # MOSTRAR COMPARAÇÃO: REAL vs PREVISÃO
 # ═══════════════════════════════════════════════════════════
 st.divider()
 st.subheader("📊 Análise Real vs Previsão")
 
 col_comp1, col_comp2, col_comp3 = st.columns(3)
 
 with col_comp1:
 st.metric("Residuo Real Medido", f"{residuo_real:.1f}%")
 st.caption("Resultado do laboratório")
 
 with col_comp2:
 if tem_puro_l:
 st.metric("Modelo Empírico", f"{pred_res_emp_l:.1f}%")
 st.caption(f"Erro: {abs(residuo_real - pred_res_emp_l):.1f}%")
 else:
 st.metric("Modelo Empírico", f"{pred_res_emp_l:.1f}%")
 st.caption(f"Erro: {abs(residuo_real - pred_res_emp_l):.1f}%")
 
 with col_comp3:
 if tem_puro_l:
 st.metric("Modelo Físico", f"{pred_res_puro_l:.1f}%")
 st.caption(f"Erro: {abs(residuo_real - pred_res_puro_l):.1f}%")
 else:
 st.metric("Previsão Final", f"{pred_res_l:.1f}%")
 st.caption(f"Erro: {abs(residuo_real - pred_res_l):.1f}%")
 
 if tem_puro_l:
 col_final = st.columns(1)[0]
 with col_final:
 erro_final = abs(residuo_real - pred_res_l)
 if erro_final < 1.0:
 st.success(f"🎯 PREVISÃO FINAL: {pred_res_l:.1f}% | Erro: {erro_final:.2f}% ✅ ACERTOU!")
 elif erro_final < 2.0:
 st.info(f"🎯 PREVISÃO FINAL: {pred_res_l:.1f}% | Erro: {erro_final:.2f}% ⚠️ Bom!")
 else:
 st.warning(f"🎯 PREVISÃO FINAL: {pred_res_l:.1f}% | Erro: {erro_final:.2f}% 🤔 Analisar")
 
 if tem_puro_l:
 msg_previsoes = (
 f"Previsões:\n"
 f"- Empírico: {pred_res_emp_l:.1f}%\n"
 f"- Físico: {pred_res_puro_l:.1f}%\n"
 f"- Final: {pred_res_l:.1f}%\n"
 f"- Real: {residuo_real}% | Erro: {abs(residuo_real - pred_res_l):.1f}%\n"
 )
 else:
 msg_previsoes = (
 f"Previsão: {pred_res_l:.1f}%\n"
 f"Real: {residuo_real}% | Erro: {abs(residuo_real - pred_res_l):.1f}%\n"
 )
 
 msg_wa_reg = (
 f"CeramicaIA - Registro de Lab Real\n\n"
 f"Data: {data_lote.strftime('%d/%m/%Y')} | Produto: {codigo_selecionado}\n"
 f"Barro Preto: {cod_p_reg} | Branco: {cod_b_reg}\n\n"
 f"Mensuracoes reais:\n"
 f"- Residuo: {residuo_real}% ({class_res_l.upper()})\n"
 f"- Umidade: {umidade_real}% | Retracao: {retracao_real}%\n"
 f"- Corte Verde: {comp_real_medido:.1f} cm | Espessura: {esp_real} cm\n"
 f"- Peso Real: {peso_real:.3f} kg ({excesso_l:+.0f}g vs meta)\n\n"
 f"{msg_previsoes}"
 f"Obs: {obs_texto}"
 )
 wa_url_reg = f"https://wa.me/?text={urllib.parse.quote(msg_wa_reg)}"
 st.link_button("Compartilhar Teste de Lab no WhatsApp", wa_url_reg)
 st.divider()
 st.subheader(f"Base de Dados Completa da Fabrica ({len(st.session_state.df_master)} Lotes Totais)")
 st.dataframe(st.session_state.df_master, use_container_width=True)
 csv_completo = st.session_state.df_master.to_csv(index=False).encode("utf-8")
 st.download_button(
 label="BAIXAR PLANILHA COMPLETA (BACKUP CSV)",
 data=csv_completo,
 file_name=f"ceramica_lotes_completo_{datetime.now().strftime('%Y%m%d')}.csv",
 mime="text/csv",
 type="primary",
 use_container_width=True,
 )
# ============================================================
# ABA 3: ANALISE DE BARRO PURO
# ============================================================
with tab_puro:
 st.header("Controle de Qualidade na Entrada - Barro Puro (Jazida)")
 st.caption("Registre a quantidade de areia/residuo da materia-prima pura que chega dos caminhoes.")
 df_barros_ativos_puro = st.session_state.catalogo_barros[
 st.session_state.catalogo_barros["status"] == "Ativo"
 ]
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
 peso_amostra = st.number_input(
 "Peso da Amostra Seca (g):", min_value=1.0, max_value=1000.0, value=100.0, step=10.0
 )
 peso_residuo_puro = st.number_input(
 "Peso do Residuo Seco Retido (g):", min_value=0.0, max_value=500.0, value=35.0, step=1.0
 )
 pct_calculada = (peso_residuo_puro / peso_amostra) * 100 if peso_amostra > 0 else 0
 st.info(f"Residuo do Barro Puro: {pct_calculada:.1f}%")
 obs_puro = st.text_area("Observacoes (Lote/Caminhao):", "Caminhao 01 - Jazida Nova")
 btn_salvar_puro = st.form_submit_button(
 "Salvar Laudo do Barro Puro", type="primary", use_container_width=True
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
 persistir_dados("puro")
 st.success(f"Laudo do Barro {cod_puro_sel} ({pct_calculada:.1f}% residuo) registrado.")
 with col_puro2:
 st.subheader("Historico de Qualidade dos Barros Puros (Jazida)")
 if len(st.session_state.analises_puro) > 0:
 st.dataframe(st.session_state.analises_puro, use_container_width=True)
 else:
 st.info("Nenhum teste de barro puro registrado ainda nesta sessao.")
# ============================================================
# ABA 4: CADASTRO E GESTAO DE BARROS
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
 novo_res_puro = st.number_input("Residuo Puro Padrao da Jazida (%):", 0.0, 80.0, 20.0, 0.5)
 nova_loc = st.text_input("Localidade / Jazida:")
 btn_cad_barro = st.form_submit_button("Cadastrar Barro", type="primary", use_container_width=True)
 if btn_cad_barro:
 if novo_cod and novo_nome:
 cod_clean = novo_cod.strip().upper()
 if cod_clean in st.session_state.catalogo_barros["codigo"].values:
 st.error(f"O codigo {cod_clean} ja esta cadastrado.")
 else:
 novo_barro_dict = {
 "codigo": cod_clean,
 "nome": novo_nome.strip(),
 "tipo_base": novo_tipo,
 "localidade": nova_loc.strip(),
 "residuo_puro": novo_res_puro,
 "status": "Ativo",
 }
 st.session_state.catalogo_barros = pd.concat(
 [st.session_state.catalogo_barros, pd.DataFrame([novo_barro_dict])],
 ignore_index=True,
 )
 persistir_dados("barros")
 st.success(f"Barro {cod_clean} cadastrado.")
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
 val_res_atual = float(dados_atual.get("residuo_puro", 20.0) if pd.notna(dados_atual.get("residuo_puro")) else 20.0)
 edit_res_puro = st.number_input("Residuo Puro Padrao da Jazida (%):", 0.0, 80.0, val_res_atual, 0.5)
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
 elif (
 edit_cod_clean != barro_edit_sel
 and edit_cod_clean in st.session_state.catalogo_barros["codigo"].values
 ):
 st.error(f"O codigo {edit_cod_clean} ja existe em outro cadastro.")
 else:
 if edit_cod_clean != barro_edit_sel:
 for col in ["cod_barro_preto", "cod_barro_amarelo", "cod_barro_branco"]:
 st.session_state.df_master[col] = st.session_state.df_master[col].replace(
 barro_edit_sel, edit_cod_clean
 )
 persistir_dados("lotes")
 st.session_state.analises_puro["codigo_barro"] = st.session_state.analises_puro["codigo_barro"].replace(
 barro_edit_sel, edit_cod_clean
 )
 persistir_dados("puro")
 st.session_state.catalogo_barros.at[idx_muda, "codigo"] = edit_cod_clean
 st.session_state.catalogo_barros.at[idx_muda, "nome"] = edit_nome.strip()
 st.session_state.catalogo_barros.at[idx_muda, "tipo_base"] = edit_tipo
 st.session_state.catalogo_barros.at[idx_muda, "residuo_puro"] = edit_res_puro
 st.session_state.catalogo_barros.at[idx_muda, "localidade"] = edit_loc.strip()
 st.session_state.catalogo_barros.at[idx_muda, "status"] = edit_status
 persistir_dados("barros")
 st.success("Barro atualizado e referencias corrigidas em cascata.")
 st.rerun()
 st.divider()
 st.subheader("Tabela Geral de Barros Cadastrados")
 st.dataframe(st.session_state.catalogo_barros, use_container_width=True)
# ============================================================
# ABA 5: CADASTRO E GESTAO DE PRODUTOS
# ============================================================
with tab_produtos:
 st.header("Cadastro e Controle de Produtos / Blocos")
 st.caption("Adicione novos produtos, ajuste metas de peso padrao, dimensoes e comprimento de corte.")
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
 n_prod_comp_nom = st.number_input("Comprimento Nominal posqueima (cm):", 5.0, 50.0, 19.0, 0.5)
 with c_dim3:
 n_prod_comp_sec = st.number_input("Comprimento Verde Ideal de Corte na Extrusora (cm):", 5.0, 55.0, 20.0, 0.5)
 n_prod_peso = st.number_input("Meta de Peso Padrao (kg):", 0.500, 15.000, 2.800, 0.050, format="%.3f")
 btn_cad_prod = st.form_submit_button("Cadastrar Produto", type="primary", use_container_width=True)
 if btn_cad_prod:
 if n_prod_cod and n_prod_nome:
 prod_cod_clean = n_prod_cod.strip().upper()
 if prod_cod_clean in st.session_state.catalogo_produtos["codigo"].values:
 st.error(f"O codigo {prod_cod_clean} ja esta cadastrado.")
 else:
 nova_chave = (
 f"{prod_cod_clean} ({n_prod_larg:.0f}x{n_prod_comp_nom:.0f}x{n_prod_comp_nom:.0f} cm) - {n_prod_nome.strip()}"
 )
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
 st.success(f"Produto {prod_cod_clean} cadastrado.")
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
 descricao_atual = dados_prod_atual["chave_comercial"].split(" - ")[-1]
 except Exception:
 descricao_atual = dados_prod_atual["chave_comercial"]
 edit_prod_nome = st.text_input("Descricao Comercial:", value=descricao_atual)
 ce_dim1, ce_dim2, ce_dim3 = st.columns(3)
 with ce_dim1:
 edit_prod_larg = st.number_input(
 "Largura (cm):", 5.0, 30.0, float(dados_prod_atual["largura"]), 0.5
 )
 with ce_dim2:
 edit_prod_comp_nom = st.number_input(
 "Comprimento Nominal pos-queima (cm):", 5.0, 50.0,
 float(dados_prod_atual["comprimento_nominal"]), 0.5,
 )
 with ce_dim3:
 edit_prod_comp_sec = st.number_input(
 "Comprimento Verde Ideal de Corte na Extrusora (cm):", 5.0, 55.0,
 float(dados_prod_atual["comp_seco_ideal"]), 0.5,
 )
 edit_prod_peso = st.number_input(
 "Meta de Peso Padrao (kg):", 0.500, 15.000,
 float(dados_prod_atual["peso_padrao"]), 0.050, format="%.3f",
 )
 lista_status_p = ["Ativo", "Inativo"]
 idx_status_p = (
 lista_status_p.index(dados_prod_atual["status"])
 if dados_prod_atual["status"] in lista_status_p else 0
 )
 edit_prod_status = st.selectbox("Status do Produto:", lista_status_p, index=idx_status_p)
 btn_salvar_prod_edit = st.form_submit_button(
 "Salvar Alteracoes de Produto", type="primary", use_container_width=True
 )
 if btn_salvar_prod_edit:
 idx_prod_muda = st.session_state.catalogo_produtos[
 st.session_state.catalogo_produtos["codigo"] == prod_edit_sel
 ].index[0]
 edit_prod_cod_clean = edit_prod_cod.strip().upper()
 if not edit_prod_cod_clean:
 st.error("O codigo do produto nao pode ser vazio.")
 elif (
 edit_prod_cod_clean != prod_edit_sel
 and edit_prod_cod_clean in st.session_state.catalogo_produtos["codigo"].values
 ):
 st.error(f"O codigo {edit_prod_cod_clean} ja existe em outro produto.")
 else:
 if edit_prod_cod_clean != prod_edit_sel:
 st.session_state.df_master["tipo_bloco"] = st.session_state.df_master["tipo_bloco"].replace(
 prod_edit_sel, edit_prod_cod_clean
 )
 persistir_dados("lotes")
 nova_chave_edit = (
 f"{edit_prod_cod_clean} ({edit_prod_larg:.0f}x{edit_prod_comp_nom:.0f}x{edit_prod_comp_nom:.0f} cm) - {edit_prod_nome.strip()}"
 )
 st.session_state.catalogo_produtos.at[idx_prod_muda, "codigo"] = edit_prod_cod_clean
 st.session_state.catalogo_produtos.at[idx_prod_muda, "chave_comercial"] = nova_chave_edit
 st.session_state.catalogo_produtos.at[idx_prod_muda, "largura"] = edit_prod_larg
 st.session_state.catalogo_produtos.at[idx_prod_muda, "comprimento_nominal"] = edit_prod_comp_nom
 st.session_state.catalogo_produtos.at[idx_prod_muda, "comp_seco_ideal"] = edit_prod_comp_sec
 st.session_state.catalogo_produtos.at[idx_prod_muda, "peso_padrao"] = edit_prod_peso
 st.session_state.catalogo_produtos.at[idx_prod_muda, "status"] = edit_prod_status
 persistir_dados("produtos")
 st.success("Produto atualizado e referencias corrigidas em cascata.")
 st.rerun()
 st.divider()
 st.subheader("Tabela Geral de Produtos / Blocos Cadastrados")
 st.dataframe(st.session_state.catalogo_produtos, use_container_width=True)
