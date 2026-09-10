# ============================================================
# CERÂMICAIÁ v3.0 — Com Compartilhamento WhatsApp e Base Unificada
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

# BASE HISTÓRICA INICIAL (110+ LOTES EMBUTIDOS NO CÓDIGO)
HISTORICO_BASE_CSV = """data,modo,preto_a,amarelo_a,branco_a,preto_b,amarelo_b,branco_b,pct_preto,pct_amarelo,pct_branco,umidade,residuo,retracao,esp_parede,peso,comprimento,tipo_bloco,class_residuo,excesso_peso,observacoes
2025-03-20,Unica,4,0,1,4,0,1,0.800,0.000,0.200,17.0,33.7,3,0.90,3.600,20.4,01-BLP,fraco,800,Histórico inicial
2025-03-21,Unica,4,0,1,4,0,1,0.800,0.000,0.200,17.0,32.0,3,0.85,3.185,20.5,01-BLP,limite,385,Histórico inicial
2025-03-24,Unica,4,0,1,4,0,1,0.800,0.000,0.200,10.0,28.0,3,0.82,3.100,20.7,01-BLP,ideal,300,Histórico inicial
2025-03-25,Unica,5,0,1,5,0,1,0.833,0.000,0.167,15.0,29.0,3,0.80,3.125,20.5,01-BLP,ideal,325,Histórico inicial
2025-03-27,Unica,5,0,1,5,0,1,0.833,0.000,0.167,16.0,31.5,3,0.85,3.184,20.5,01-BLP,ideal,384,Histórico inicial
2025-03-28,Unica,5,0,1,5,0,1,0.833,0.000,0.167,16.0,28.7,3,0.77,3.074,20.0,01-BLP,ideal,274,Histórico inicial
2025-04-02,Unica,5,0,1,5,0,1,0.833,0.000,0.167,14.0,29.2,4,0.80,3.244,20.7,01-BLP,ideal,444,Histórico inicial
2025-04-03,Unica,5,0,1,5,0,1,0.833,0.000,0.167,16.0,30.0,3,0.87,3.114,20.2,01-BLP,ideal,314,Histórico inicial
2025-04-09,Unica,5,0,1,5,0,1,0.833,0.000,0.167,15.0,30.9,4,0.82,3.231,20.0,01-BLP,ideal,431,Histórico inicial
2025-04-10,Unica,5,0,1,5,0,1,0.833,0.000,0.167,14.0,33.5,4,0.90,3.237,20.0,01-BLP,fraco,437,Histórico inicial
2025-04-16,Unica,5,0,1,5,0,1,0.833,0.000,0.167,13.0,28.6,4,0.77,3.277,20.5,01-BLP,ideal,477,Histórico inicial
2025-04-18,Unica,5,0,1,5,0,1,0.833,0.000,0.167,16.0,28.4,3,0.85,3.390,20.6,01-BLP,ideal,590,Histórico inicial
2025-04-30,Unica,5,0,1,5,0,1,0.833,0.000,0.167,12.0,28.4,3,0.95,3.390,20.6,01-BLP,ideal,590,Histórico inicial
2025-05-14,Unica,4,0,1,4,0,1,0.800,0.000,0.200,12.0,32.0,3,0.80,3.419,20.2,01-BLP,limite,619,Histórico inicial
2025-05-15,Unica,4,0,1,4,0,1,0.800,0.000,0.200,11.0,32.6,3,0.725,2.885,20.0,01-BLP,fraco,85,Histórico inicial
2025-05-16,Unica,4,0,1,4,0,1,0.800,0.000,0.200,13.0,33.3,3,0.80,2.930,20.0,01-BLP,fraco,130,Histórico inicial
2025-05-22,Unica,4,0,1,4,0,1,0.800,0.000,0.200,10.0,33.3,3,0.80,3.050,20.0,01-BLP,fraco,250,Histórico inicial
2025-05-26,Unica,4,0,1,4,0,1,0.800,0.000,0.200,16.0,34.0,2,0.725,3.071,20.6,01-BLP,fraco,271,Histórico inicial
2025-05-28,Unica,4,0,1,4,0,1,0.800,0.000,0.200,12.0,34.5,3,0.775,3.055,20.0,01-BLP,fraco,255,Histórico inicial
2025-05-30,Unica,4,0,1,4,0,1,0.800,0.000,0.200,12.0,32.7,4,0.975,3.025,20.0,01-BLP,fraco,225,Histórico inicial
2025-06-05,Unica,4,0,1,4,0,1,0.800,0.000,0.200,12.0,32.0,4,0.56,3.184,20.0,01-BLP,limite,384,Histórico inicial
2025-06-10,Unica,4,0,1,4,0,1,0.800,0.000,0.200,14.0,30.9,4,0.725,3.175,20.5,01-BLP,ideal,375,Histórico inicial
2025-06-17,Unica,5,0,1,5,0,1,0.833,0.000,0.167,13.0,33.0,3,0.725,3.315,20.5,01-BLP,fraco,515,Histórico inicial
2025-06-25,Unica,5,0,1,5,0,1,0.833,0.000,0.167,13.0,30.2,3,0.775,3.284,20.5,01-BLP,ideal,484,Histórico inicial
2025-07-04,Unica,5,0,1,5,0,1,0.833,0.000,0.167,12.0,28.1,4,0.725,3.284,20.5,01-BLP,ideal,484,Histórico inicial
2025-07-07,Unica,5,0,1,5,0,1,0.833,0.000,0.167,12.0,31.5,3,0.775,3.400,20.7,01-BLP,ideal,600,Histórico inicial
2025-07-09,Unica,5,0,1,5,0,1,0.833,0.000,0.167,12.0,29.6,5,0.70,3.100,20.5,01-BLP,ideal,300,Histórico inicial
2025-07-10,Unica,5,0,1,5,0,1,0.833,0.000,0.167,14.0,31.0,4,0.725,3.084,20.2,01-BLP,ideal,284,Histórico inicial
2025-07-14,Unica,5,0,1,5,0,1,0.833,0.000,0.167,15.0,30.0,4,0.675,3.090,20.0,01-BLP,ideal,290,Histórico inicial
2025-07-28,Unica,5,0,1,5,0,1,0.833,0.000,0.167,15.0,36.6,4,0.725,3.227,20.3,01-BLP,fraco,427,Histórico inicial
2025-08-05,Unica,5,0,1,5,0,1,0.833,0.000,0.167,15.0,36.0,4,0.80,3.241,20.3,01-BLP,fraco,441,Histórico inicial
2025-08-11,Unica,5,0,1,5,0,1,0.833,0.000,0.167,14.0,29.5,4,0.725,3.300,20.3,01-BLP,ideal,500,Histórico inicial
2025-08-18,Unica,5,0,1,5,0,1,0.833,0.000,0.167,14.0,32.0,4,0.675,3.020,20.1,01-BLP,limite,220,Histórico inicial
2025-08-19,Unica,5,0,1,5,0,1,0.833,0.000,0.167,11.0,31.0,3,0.675,3.000,20.0,01-BLP,ideal,200,Histórico inicial
2025-08-21,Unica,5,0,1,5,0,1,0.833,0.000,0.167,13.0,34.0,3,0.65,3.048,20.3,01-BLP,fraco,248,Histórico inicial
2025-09-02,Mesclada,5,0,1,4,0,1,0.817,0.000,0.183,15.0,31.5,4,0.575,3.097,20.1,01-BLP,ideal,297,Histórico inicial
2025-09-16,Mesclada,5,0,1,4,0,1,0.817,0.000,0.183,18.0,29.0,4,0.625,3.338,20.1,01-BLP,ideal,538,Histórico inicial
2025-09-23,Mesclada,5,0,1,4,0,1,0.817,0.000,0.183,16.0,28.5,4,0.725,3.149,20.3,01-BLP,ideal,349,Histórico inicial
2025-09-25,Mesclada,5,0,1,4,0,1,0.817,0.000,0.183,15.0,28.0,3,0.825,3.400,20.1,01-BLP,ideal,600,Histórico inicial
2025-09-30,Mesclada,5,0,1,4,0,1,0.817,0.000,0.183,17.0,28.0,4,0.75,3.291,20.1,01-BLP,ideal,491,Histórico inicial
2025-10-05,Mesclada,5,0,1,4,0,1,0.817,0.000,0.183,17.0,28.0,4,0.75,6.000,40.0,03-BLQ,ideal,0,Histórico inicial
2025-10-15,Mesclada,5,0,1,4,0,1,0.817,0.000,0.183,17.0,28.0,4,0.75,6.300,40.0,02-BLG,ideal,800,Histórico inicial
2025-12-24,Unica,3,0,2,3,0,2,0.600,0.000,0.400,18.0,28.0,3,0.60,3.016,21.0,01-BLP,ideal,216,Histórico inicial
2025-12-26,Unica,3,0,2,3,0,2,0.600,0.000,0.400,18.0,30.0,3,0.60,2.891,20.0,01-BLP,ideal,91,Histórico inicial
2025-12-27,Unica,3,0,2,3,0,2,0.600,0.000,0.400,18.0,35.0,3,0.60,6.089,41.0,02-BLG,fraco,589,Histórico inicial
2025-12-29,Unica,3,0,2,3,0,2,0.600,0.000,0.400,18.0,34.0,3,0.60,6.102,41.0,02-BLG,fraco,602,Histórico inicial
2025-12-30,Unica,3,0,2,3,0,2,0.600,0.000,0.400,17.0,42.0,3,0.60,3.132,21.0,01-BLP,fraco,332,Histórico inicial
2026-01-02,Unica,4,0,2,4,0,2,0.667,0.000,0.333,18.0,32.0,3,0.60,3.116,20.0,01-BLP,limite,316,Histórico inicial
2026-01-12,Unica,4,0,2,4,0,2,0.667,0.000,0.333,16.0,38.0,3,0.60,6.360,41.0,02-BLG,fraco,860,Histórico inicial
2026-01-13,Unica,4,0,2,4,0,2,0.667,0.000,0.333,17.0,26.0,3,0.60,6.303,41.0,02-BLG,forte,803,Histórico inicial
2026-01-14,Unica,4,0,2,4,0,2,0.667,0.000,0.333,17.0,36.0,3,0.60,3.175,21.0,01-BLP,fraco,375,Histórico inicial
2026-01-15,Unica,4,0,2,4,0,2,0.667,0.000,0.333,18.0,35.0,3,0.60,3.077,20.0,01-BLP,fraco,277,Histórico inicial
2026-01-20,Unica,6,0,3,6,0,3,0.667,0.000,0.333,12.0,32.0,3,0.70,2.605,40.0,02-BLG,limite,-2895,Histórico inicial
2026-01-21,Unica,6,0,3,6,0,3,0.667,0.000,0.333,17.0,37.0,3,0.60,3.170,21.0,01-BLP,fraco,370,Histórico inicial
2026-01-23,Unica,3,0,1,3,0,1,0.750,0.000,0.250,13.0,30.0,3,0.60,3.071,20.0,01-BLP,ideal,271,Histórico inicial
2026-01-27,Unica,3,0,1,3,0,1,0.750,0.000,0.250,13.0,27.0,3,0.60,3.134,20.0,01-BLP,forte,334,Histórico inicial
2026-01-28,Unica,3,0,1,3,0,1,0.750,0.000,0.250,13.0,30.0,3,0.60,6.357,41.0,02-BLG,ideal,857,Histórico inicial
2026-02-06,Mesclada,3,0,1,3,0,2,0.675,0.000,0.325,12.0,26.0,3,0.60,6.450,41.0,02-BLG,forte,950,Histórico inicial
2026-02-10,Unica,3,0,2,3,0,2,0.600,0.000,0.400,12.0,30.0,3,0.60,6.401,41.0,02-BLG,ideal,901,Histórico inicial
2026-02-11,Unica,3,0,2,3,0,2,0.600,0.000,0.400,12.0,29.0,3,0.60,6.705,41.0,02-BLG,ideal,1205,Histórico inicial
2026-02-18,Unica,3,0,2,3,0,2,0.600,0.000,0.400,12.0,28.0,3,0.60,6.571,41.0,02-BLG,ideal,1071,Histórico inicial
2026-02-19,Unica,3,0,3,3,0,3,0.500,0.000,0.500,12.0,30.0,3,0.60,6.498,41.0,02-BLG,ideal,998,Histórico inicial
2026-02-19,Unica,3,0,3,3,0,3,0.500,0.000,0.500,11.0,37.0,3,0.60,6.596,41.0,02-BLG,fraco,1096,Histórico inicial
2026-02-20,Unica,3,0,3,3,0,3,0.500,0.000,0.500,12.0,32.0,3,0.60,3.121,19.0,01-BLP,limite,321,Histórico inicial
2026-02-23,Unica,3,0,3,3,0,3,0.500,0.000,0.500,14.0,30.0,3,0.60,3.268,20.0,01-BLP,ideal,468,Histórico inicial
2026-03-04,Unica,3,0,2,3,0,2,0.600,0.000,0.400,12.0,33.0,3,0.60,6.380,41.0,02-BLG,fraco,880,Histórico inicial
2026-03-07,Unica,3,0,2,3,0,2,0.600,0.000,0.400,12.0,33.0,3,0.60,3.279,20.0,01-BLP,fraco,479,Histórico inicial
2026-03-09,Unica,3,0,2,3,0,2,0.600,0.000,0.400,13.0,33.0,3,0.60,6.317,40.0,02-BLG,fraco,817,Histórico inicial
2026-03-23,Unica,3,0,2,3,0,2,0.600,0.000,0.400,11.0,37.0,3,0.60,3.335,20.0,01-BLP,fraco,535,Histórico inicial
2026-03-27,Unica,3,0,2,3,0,2,0.600,0.000,0.400,14.0,30.0,3,0.60,3.386,20.0,01-BLP,ideal,586,Histórico inicial
2026-04-01,Unica,3,0,2,3,0,2,0.600,0.000,0.400,12.0,37.0,3,0.60,6.593,41.0,02-BLG,fraco,1093,Histórico inicial
2026-04-07,Unica,3,0,2,3,0,2,0.600,0.000,0.400,10.0,36.0,3,0.60,3.362,20.0,01-BLP,fraco,562,Histórico inicial
2026-04-15,Mesclada,3,0,1,3,0,2,0.675,0.000,0.325,12.0,33.0,3,0.60,6.580,40.0,02-BLG,fraco,1080,Histórico inicial
2026-04-22,Unica,3,0,1,3,0,1,0.750,0.000,0.250,12.0,37.0,3,0.60,3.394,20.0,01-BLP,fraco,594,Histórico inicial
2026-04-27,Unica,4,0,1,4,0,1,0.800,0.000,0.200,12.0,28.0,3,0.60,3.311,20.0,01-BLP,ideal,511,Histórico inicial
2026-04-29,Mesclada,3,0,1,4,0,1,0.775,0.000,0.225,12.0,37.0,3,0.60,6.878,40.0,02-BLG,fraco,1378,Histórico inicial
2026-05-05,Mesclada,3,0,1,4,0,1,0.775,0.000,0.225,12.0,33.0,3,0.60,3.541,20.0,01-BLP,fraco,741,Histórico inicial
2026-05-07,Unica,3,0,1,3,0,1,0.750,0.000,0.250,12.0,32.0,3,0.60,3.475,20.0,01-BLP,limite,675,Histórico inicial
2026-05-13,Unica,3,0,1,3,0,1,0.750,0.000,0.250,12.0,32.0,3,0.60,3.530,20.0,01-BLP,limite,730,Histórico inicial
2026-05-18,Unica,4,0,1,4,0,1,0.800,0.000,0.200,12.0,31.0,3,0.60,8.200,41.0,BG14,ideal,1200,Histórico inicial
2026-05-19,Unica,4,0,1,4,0,1,0.800,0.000,0.200,15.0,31.0,3,0.60,3.570,20.0,01-BLP,ideal,770,Histórico inicial
2026-05-21,Unica,4,0,1,4,0,1,0.800,0.000,0.200,20.0,32.0,3,0.60,3.618,20.0,01-BLP,limite,818,Histórico inicial
2026-05-27,Unica,3,0,1,3,0,1,0.750,0.000,0.250,12.0,28.0,3,0.60,3.540,41.0,02-BLG,ideal,-1960,Histórico inicial
2026-06-13,Unica,3,0,1,3,0,1,0.750,0.000,0.250,12.0,27.5,2,0.60,6.700,41.0,02-BLG,forte,1200,Histórico inicial
2026-06-15,Unica,3,0,1,3,0,1,0.750,0.000,0.250,20.0,30.3,3,0.23,3.633,20.0,01-BLP,ideal,833,Histórico inicial
2026-06-16,Unica,3,0,1,3,0,1,0.750,0.000,0.250,12.0,29.5,4,0.23,3.670,20.5,01-BLP,ideal,870,Histórico inicial
2026-06-17,Unica,3,0,1,3,0,1,0.750,0.000,0.250,17.0,31.6,3,0.75,7.000,41.0,BG14,ideal,0,Histórico inicial
2026-06-18,Unica,3,0,1,3,0,1,0.750,0.000,0.250,18.0,30.8,3,0.75,3.300,20.3,01-BLP,ideal,500,Histórico inicial
2026-06-19,Unica,3,0,1,3,0,1,0.750,0.000,0.250,15.7,31.6,3,0.86,6.700,19.1,BP14,ideal,2900,Histórico inicial
2026-06-20,Unica,3,0,1,3,0,1,0.750,0.000,0.250,20.0,31.8,3,0.76,3.576,19.8,01-BLP,ideal,776,Histórico inicial
2026-06-22,Unica,4,0,1,4,0,1,0.800,0.000,0.200,15.9,28.2,3,0.80,3.570,20.1,01-BLP,ideal,770,Histórico inicial
2026-06-23,Unica,4,0,1,4,0,1,0.800,0.000,0.200,17.0,28.5,3,0.88,3.500,20.2,01-BLP,ideal,700,Histórico inicial
2026-06-24,Mesclada,4,0,1,4,0,2,0.733,0.000,0.267,15.0,27.6,4,0.83,3.570,20.4,01-BLP,forte,770,Histórico inicial
2026-06-25,Mesclada,4,0,1,5,0,2,0.757,0.000,0.243,18.0,29.0,3,0.75,3.500,20.0,01-BLP,ideal,700,Histórico inicial
2026-06-26,Unica,3,0,1,3,0,1,0.750,0.000,0.250,18.5,32.7,3,0.83,3.715,20.5,01-BLP,fraco,915,Histórico inicial
2026-06-27,Unica,4,0,1,4,0,1,0.800,0.000,0.200,14.9,30.7,3,0.85,3.680,20.5,01-BLP,ideal,880,Histórico inicial
2026-06-28,Unica,4,0,1,4,0,1,0.800,0.000,0.200,16.0,31.0,3,0.60,3.252,20.0,01-BLP,ideal,452,Histórico inicial
2026-06-29,Unica,4,0,1,4,0,1,0.800,0.000,0.200,15.0,32.0,3,0.58,5.500,20.3,02-BLG,limite,0,Histórico inicial
2026-07-02,Unica,3,0,1,3,0,1,0.750,0.000,0.250,12.5,30.0,3,0.90,3.716,20.3,01-BLP,ideal,916,Histórico inicial
2026-07-06,Unica,3,0,1,3,0,1,0.750,0.000,0.250,15.3,29.0,3,0.73,3.518,20.8,01-BLP,ideal,718,Histórico inicial
2026-07-07,Unica,3,0,1,3,0,1,0.750,0.000,0.250,16.0,31.4,2,0.73,6.900,40.3,BG14,ideal,-100,Histórico inicial
2026-07-08,Unica,3,0,1,3,0,1,0.750,0.000,0.250,15.0,33.4,3,0.73,7.200,40.9,BG14,fraco,200,Histórico inicial
2026-07-10,Unica,3,0,1,3,0,1,0.750,0.000,0.250,15.2,31.9,3,0.73,6.980,40.5,BG14,ideal,-20,Histórico inicial
2026-07-11,Unica,3,0,1,3,0,1,0.750,0.000,0.250,17.6,31.8,4,0.70,5.585,20.2,02-BLG,ideal,85,Histórico inicial
2026-07-13,Mesclada,3,0,1,4,0,1,0.775,0.000,0.225,17.9,31.1,3,0.83,3.525,20.0,01-BLP,ideal,725,Histórico inicial
2026-07-15,Unica,4,0,1,4,0,1,0.800,0.000,0.200,16.5,32.2,2,0.78,3.539,20.0,01-BLP,fraco,739,Histórico inicial
2026-07-16,Unica,5,0,1,5,0,1,0.833,0.000,0.167,18.0,32.2,3,0.80,3.585,20.2,01-BLP,fraco,785,Histórico inicial
2026-07-18,Unica,5,0,1,5,0,1,0.833,0.000,0.167,19.0,32.7,3,0.85,3.535,20.7,01-BLP,fraco,735,Histórico inicial
2026-07-20,Unica,5,0,1,5,0,1,0.833,0.000,0.167,19.0,26.0,3,0.85,3.500,20.5,01-BLP,forte,700,Histórico inicial
2026-07-21,Unica,4,0,1,4,0,1,0.800,0.000,0.200,15.9,28.2,3,0.80,3.570,20.1,01-BLP,ideal,770,Histórico inicial
2026-07-22,Unica,4,0,1,4,0,1,0.800,0.000,0.200,17.8,28.5,3,0.88,3.550,20.2,01-BLP,ideal,750,Histórico inicial
2026-07-23,Mesclada,4,0,1,4,0,2,0.733,0.000,0.267,13.8,28.8,3,0.83,3.500,20.2,01-BLP,ideal,700,Histórico inicial
2026-07-25,Mesclada,4,0,1,5,0,2,0.757,0.000,0.243,15.0,27.6,4,0.83,3.570,20.4,01-BLP,forte,770,Histórico inicial
2026-07-27,Unica,4,0,1,4,0,1,0.800,0.000,0.200,14.9,30.7,3,0.75,3.680,20.5,01-BLP,ideal,880,Histórico inicial
2026-07-28,Unica,4,0,1,4,0,1,0.800,0.000,0.200,16.0,31.0,3,0.60,3.252,20.0,01-BLP,ideal,452,Histórico inicial
2026-07-29,Unica,4,0,1,4,0,1,0.800,0.000,0.200,15.0,32.0,3,0.58,5.500,20.3,02-BLG,limite,0,Histórico inicial
2026-07-31,Unica,4,0,1,4,0,1,0.800,0.000,0.200,15.0,32.0,3,0.58,3.500,20.3,01-BLP,limite,700,Histórico inicial
2026-08-03,Unica,4,0,1,4,0,1,0.800,0.000,0.200,17.5,33.0,3,0.63,2.825,20.5,01-BLP,fraco,25,Histórico inicial
2026-08-05,Unica,1,0,1,1,0,1,0.500,0.000,0.500,15.5,25.0,3,0.58,2.800,20.1,01-BLP,forte,0,Histórico inicial
2026-08-06,Unica,5,0,1,5,0,1,0.833,0.000,0.167,16.0,24.7,3,0.53,2.837,20.5,01-BLP,forte,37,Histórico inicial
2026-08-08,Unica,4,0,1,4,0,1,0.800,0.000,0.200,18.0,31.0,3,0.63,2.817,20.5,01-BLP,ideal,17,Histórico inicial
2026-08-10,Unica,4,0,1,4,0,1,0.800,0.000,0.200,17.0,29.1,3,0.70,6.520,40.4,BG14,ideal,-480,Histórico inicial
2026-08-12,Unica,4,0,1,4,0,1,0.800,0.000,0.200,13.0,27.6,3,0.65,2.842,20.5,01-BLP,forte,42,Histórico inicial
2026-08-17,Unica,4,0,1,4,0,1,0.800,0.000,0.200,15.0,28.0,4,0.63,2.817,20.2,01-BLP,ideal,17,Histórico inicial
2026-08-19,Unica,4,0,1,4,0,1,0.800,0.000,0.200,18.0,29.2,3,0.80,6.800,40.5,BG14,ideal,-200,Histórico inicial
2026-08-20,Unica,4,0,1,4,0,1,0.800,0.000,0.200,17.0,28.8,3,0.60,2.865,20.5,01-BLP,ideal,65,Histórico inicial
2026-08-21,Unica,4,0,1,4,0,1,0.800,0.000,0.200,17.9,27.7,3,0.60,2.840,20.3,01-BLP,forte,40,Histórico inicial
2026-08-25,Unica,4,0,1,4,0,1,0.800,0.000,0.200,17.6,29.0,3,0.60,2.850,20.5,01-BLP,ideal,50,Histórico inicial
2026-08-26,Unica,4,0,1,4,0,1,0.800,0.000,0.200,19.0,26.0,5,0.60,2.880,20.4,01-BLP,forte,80,Histórico inicial
2026-08-27,Mesclada,2,0,1,4,0,1,0.733,0.000,0.267,19.5,22.0,3,0.60,2.817,20.5,01-BLP,forte,17,Histórico inicial
2026-08-27,Unica,3,0,1,3,0,1,0.750,0.000,0.250,16.1,27.5,3,0.69,2.831,20.3,01-BLP,forte,31,Histórico inicial
2026-09-02,Mesclada,3,1,1,3,1,2,0.550,0.183,0.267,17.0,30.0,3,0.68,2.935,20.3,01-BLP,ideal,135,Histórico inicial
2026-09-07,Mesclada,3,1,1,3,1,2,0.550,0.183,0.267,17.7,31.1,3,0.61,5.780,40.5,02-BLG,ideal,280,Histórico inicial
2026-09-08,Mesclada,3,1,1,3,1,2,0.550,0.183,0.267,17.8,31.3,3,0.65,2.990,20.4,01-BLP,ideal,190,Histórico inicial
2026-09-09,Mesclada,3,1,1,3,1,2,0.550,0.183,0.267,16.2,32.5,4,0.65,2.960,20.4,01-BLP,fraco,160,Histórico inicial"""

# INICIALIZAR BASE DE DADOS EM MEMÓRIA (st.session_state)
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

# CRIAR ABAS
tab_diag, tab_reg = st.tabs(["🔮 Diagnóstico & Previsão", "📝 Registrar Análise Real (Alimentar IA)"])

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

    st.header("🏗️ Composição da Mistura")

    modo = st.radio("Tipo de Produção do Dia:", ["Receita Única", "Mistura Mesclada (Alternada)"], horizontal=True)

    if modo == "Receita Única":
        c1, c2, c3 = st.columns(3)
        with c1: preto_a = st.number_input("Conchas de PRETO (BSV)", 0, 10, 4, 1)
        with c2: amarelo_a = st.number_input("Conchas de AMARELO", 0, 10, 0, 1)
        with c3: branco_a = st.number_input("Conchas de BRANCO", 0, 10, 1, 1)
        
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

    st.caption(f"📊 **Massa Resultante na Maromba:** {pct_preto*100:.1f}% Preto | {pct_amarelo*100:.1f}% Amarelo | {pct_branco*100:.1f}% Branco")

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

        # BOTÃO COMPARTILHAR WHATSAPP
        st.divider()
        msg_wa_diag = f"""🧱 *CerâmicaIA — Diagnóstico de Mistura*
        
📌 *Produto:* {codigo_prod} ({largura_cm}x19x{comprimento_cm}cm)
🧱 *Mistura:* {mistura_desc}
💧 *Umidade:* {umidade}% | 📏 *Esp. Parede:* {esp_parede}cm

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
    st.caption("Alimente o sistema com os dados reais medidos para enriquecer a Inteligência da fábrica.")
    
    with st.form("form_registro_lote", clear_on_submit=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            data_lote = st.date_input("Data do Teste", datetime.now())
            prod_lote = st.selectbox("Produto Testado", list(CATALOGO_PRODUTOS.keys()))
            codigo_selecionado = CATALOGO_PRODUTOS[prod_lote]["codigo"]
            comprimento_selecionado = CATALOGO_PRODUTOS[prod_lote]["comprimento"]
        with f_col2:
            modo_lote = st.selectbox("Tipo de Produção", ["Unica", "Mesclada"])
            p_a = st.number_input("Preto A", 0, 10, 4)
            a_a = st.number_input("Amarelo A", 0, 10, 0)
            b_a = st.number_input("Branco A", 0, 10, 1)
        with f_col3:
            p_b = st.number_input("Preto B (se mesclada)", 0, 10, p_a)
            a_b = st.number_input("Amarelo B (se mesclada)", 0, 10, a_a)
            b_b = st.number_input("Branco B (se mesclada)", 0, 10, b_a)

        f_col4, f_col5, f_col6, f_col7 = st.columns(4)
        with f_col4: umidade_real = st.number_input("Umidade Real (%)", 0.0, 40.0, 16.0, 0.1)
        with f_col5: residuo_real = st.number_input("Resíduo Real (%)", 0.0, 50.0, 30.0, 0.1)
        with f_col6: retracao_real = st.number_input("Retração Real (%)", 0.0, 10.0, 3.0, 0.1)
        with f_col7: esp_real = st.number_input("Espessura Parede (cm)", 0.0, 2.0, 0.65, 0.01)

        f_col8, f_col9 = st.columns(2)
        with f_col8: peso_real = st.number_input("Peso Real Medido (kg)", 0.0, 15.0, 3.100, 0.001)
        with f_col9: obs_texto = st.text_area("💬 Observações (ex: 'barro mais arenoso', 'trocou fita da maromba', 'curtiu 2 dias'):", "Teste de rotina")
        
        btn_salvar = st.form_submit_button("💾 Salvar Registro e Unificar Base", type="primary", use_container_width=True)
        
        if btn_salvar:
            # Calcular percentuais ponderados
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
                "preto_a": p_a, "amarelo_a": a_a, "branco_a": b_a,
                "preto_b": p_b, "amarelo_b": a_b, "branco_b": b_b,
                "pct_preto": round(pct_p_l, 3), "pct_amarelo": round(pct_a_l, 3), "pct_branco": round(pct_b_l, 3),
                "umidade": umidade_real, "residuo": residuo_real, "retracao": retracao_real,
                "esp_parede": esp_real, "peso": peso_real, "comprimento": comprimento_selecionado,
                "tipo_bloco": codigo_selecionado, "class_residuo": class_res_l, "excesso_peso": round(excesso_l, 0),
                "observacoes": obs_texto
            }
            
            # Adiciona à base em memória
            st.session_state.df_master = pd.concat([pd.DataFrame([novo_row]), st.session_state.df_master], ignore_index=True)
            st.success("✅ Lote registrado com sucesso! A base completa foi atualizada.")

            # BOTÃO DE WHATSAPP PARA REGISTRO REAL
            msg_wa_reg = f"""📝 *CerâmicaIA — Registro de Laboratório Real*
            
📌 *Data:* {data_lote.strftime('%d/%m/%Y')} | *Produto:* {codigo_selecionado}
🧪 *MENSURAÇÕES REAIS:*
• *Resíduo:* {residuo_real}% ({class_res_l.upper()})
• *Umidade:* {umidade_real}% | *Retração:* {retracao_real}%
• *Peso Real:* {peso_real:.3f} kg ({excesso_l:+.0f}g vs meta)
• *Espessura:* {esp_real} cm

💬 *Obs:* {obs_texto}"""

            wa_url_reg = f"https://wa.me/?text={urllib.parse.quote(msg_wa_reg)}"
            st.link_button("📲 Compartilhar Teste de Lab no WhatsApp", wa_url_reg)

    # EXIBIÇÃO DA BASE COMPLETA ATUALIZADA
    st.divider()
    st.subheader(f"📋 Base de Dados Completa da Fábrica ({len(st.session_state.df_master)} Lotes Totais)")
    st.caption("Esta tabela contém o histórico antigo unificado com todos os novos registros efetuados.")
    
    st.dataframe(st.session_state.df_master, use_container_width=True)
    
    # BOTÃO PARA BAIXAR O CSV COMPLETO PRONTO PRO COLAB
    csv_completo = st.session_state.df_master.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 BAIXAR PLANILHA COMPLETA ATUALIZADA PARA RE-TREINO NA IA (CSV)",
        data=csv_completo,
        file_name=f"ceramica_lotes_completo_para_colab_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True
    )
