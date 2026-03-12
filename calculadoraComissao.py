import streamlit as st
import itertools
import pandas as pd
import io

st.set_page_config(layout="wide", page_title="Simulador M1", page_icon="🟩")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #00A859 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #00A859;'>🟩 Simulador de Metas - M1</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px; color: #555;'>Projete seu mix de clientes e maximize seus ganhos com inteligência.</p>", unsafe_allow_html=True)
st.divider()

DADOS_COMISSAO_BASE = {
    "10k (Agressiva)": {"valor": 90, "tpv":10000},
    "10k (Mais Agressiva)":  {"valor": 90,  "tpv": 10000},
    "10k (Menos Agressiva)": {"valor": 90,  "tpv": 10000}, 
    "30k (Agressiva)":  {"valor": 260, "tpv": 30000},
    "30k (Mais Agressiva)":  {"valor": 170, "tpv": 30000},
    "30k (Menos Agressiva)": {"valor": 360, "tpv": 30000}, 
    "50k (Agressiva)":  {"valor": 340, "tpv": 50000},
    "50k (Mais Agressiva)":  {"valor": 210, "tpv": 50000},
    "50k (Menos Agressiva)": {"valor": 470, "tpv": 50000}, 
    "100k (Agressiva)": {"valor": 850, "tpv": 100000},
    "100k (Mais Agressiva)": {"valor": 430, "tpv": 100000},
    "100k (Menos Agressiva)":{"valor": 1280, "tpv": 100000} 
}

def obter_multiplicador(tpv_total, meta_mes):
    if meta_mes == 0: return 1.0 
    atingimento = tpv_total / meta_mes
    if atingimento < 0.4: return 0.4
    elif atingimento < 0.6: return 0.6
    elif atingimento < 0.8: return 0.8
    elif atingimento < 1.0: return 0.8  
    elif atingimento < 1.2: return 1.2  
    elif atingimento < 1.4: return 1.4
    elif atingimento < 1.6: return 1.6
    elif atingimento < 1.8: return 1.8
    return 2.0

def calcular_cenario(quantidades, dados_filtrados, meta_tpv):
    tpv_total = sum(quantidades[tipo] * dados_filtrados[tipo]["tpv"] for tipo in quantidades)
    comissao_bruta = sum(quantidades[tipo] * dados_filtrados[tipo]["valor"] for tipo in quantidades)
    multiplicador = obter_multiplicador(tpv_total, meta_tpv)
    return tpv_total, comissao_bruta * multiplicador, multiplicador

def simular_combinacoes(meta_dinheiro, limites_tpv, estrategia, meta_tpv, dados_filtrados):
    tipos_clientes = list(dados_filtrados.keys())
    ranges_list = []
    for t in tipos_clientes:
        if "10k" in t: ranges_list.append(range(limites_tpv["10k"] + 1))
        elif "30k" in t: ranges_list.append(range(limites_tpv["30k"] + 1))
        elif "50k" in t: ranges_list.append(range(limites_tpv["50k"] + 1))
        elif "100k" in t: ranges_list.append(range(limites_tpv["100k"] + 1))

    cenarios_encontrados = []
    for quantidades_tupla in itertools.product(*ranges_list):
        q_dict = dict(zip(tipos_clientes, quantidades_tupla))
        valido = True
        for cat in ["10k", "30k", "50k", "100k"]:
            soma_cat = sum(v for k, v in q_dict.items() if k.startswith(cat))
            if soma_cat > limites_tpv[cat]:
                valido = False
                break
        if not valido: continue
        tpv, comissao, mult = calcular_cenario(q_dict, dados_filtrados, meta_tpv)
        if comissao >= meta_dinheiro:
            cenarios_encontrados.append({
                "mix": q_dict, "tpv_total": tpv, "comissao_final": comissao, 
                "multiplicador": mult, "total_clientes": sum(q_dict.values())
            })
    sort_key = (lambda x: (x['tpv_total'], x['total_clientes'])) if estrategia == "🎯 Menor Volume de TPV" else (lambda x: (x['total_clientes'], x['tpv_total']))
    cenarios_encontrados.sort(key=sort_key)
    return cenarios_encontrados

with st.sidebar:
    st.header("⚙️ Parâmetros")
    meta_tpv_mes = st.number_input("📈 Meta de TPV do Agente (R$)", min_value=1.0, value=300000.0, step=10000.0)
    meta_desejada = st.number_input("💰 Meta de Comissão (R$)", min_value=1.0, value=5000.0, step=500.0)
    st.divider()
    st.subheader("📑 Seleção de Ofertas")
    ofertas_selecionadas = st.multiselect(
        "Quais ofertas deseja incluir?",
        options=list(DADOS_COMISSAO_BASE.keys()),
        default=list(DADOS_COMISSAO_BASE.keys())
    )
    st.divider()
    st.subheader("⏱️ Mix de Clientes (Máximos)")
    limite_geral = st.slider("Max Clientes (10k, 30k e 50k)", 0, 8, 3)
    l100 = st.slider("Max Clientes 100k", 0, 5, 1)
    limites_tpv = {"10k": limite_geral, "30k": limite_geral, "50k": limite_geral, "100k": l100}
    st.divider()
    estrategia_escolhida = st.radio("🎯 Estratégia", ["🎯 Menor Volume de TPV", "🚀 Menos Clientes"])
    btn_simular = st.button("🚀 Gerar Cenários", use_container_width=True, type="primary")

if btn_simular:
    if not ofertas_selecionadas:
        st.error("Por favor, selecione pelo menos uma oferta para simular.")
    elif meta_desejada > 0 and meta_tpv_mes > 0:
        dados_filtrados = {k: v for k, v in DADOS_COMISSAO_BASE.items() if k in ofertas_selecionadas}
        with st.spinner("Analisando a matriz personalizada..."):
            cenarios = simular_combinacoes(meta_desejada, limites_tpv, estrategia_escolhida, meta_tpv_mes, dados_filtrados)
        if cenarios:
            st.toast("Simulação concluída!", icon="✅")
            melhor = cenarios[0]
            st.markdown("### 🏆 Melhor Cenário Sugerido")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Comissão Final", f"R$ {melhor['comissao_final']:,.2f}")
            m2.metric("TPV Total", f"R$ {melhor['tpv_total']:,.2f}")
            m3.metric("Mult.", f"{melhor['multiplicador']}x")
            m4.metric("Total Clientes", melhor['total_clientes'])
            mix_txt = " | ".join([f"{v}x {k}" for k, v in melhor['mix'].items() if v > 0])
            st.info(f"**Mix Sugerido:** {mix_txt}")
            st.divider()
            st.markdown("### 📋 Outras Opções Viáveis")
            df = pd.DataFrame([{
                "Mix Sugerido": " | ".join([f"{v}x {k}" for k, v in c['mix'].items() if v > 0]),
                "Qtd Clientes": c['total_clientes'],
                "TPV Total": f"R$ {c['tpv_total']:,.2f}",
                "Mult.": f"{c['multiplicador']}x",
                "Comissão": f"R$ {c['comissao_final']:,.2f}"
            } for c in cenarios[1:51]])
            st.dataframe(df, use_container_width=True)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Cenarios')
            st.download_button("📥 Baixar Excel", buffer.getvalue(), "simulacao_stone.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("Nenhum cenário encontrado com as ofertas selecionadas.")
else:
    st.info("👈 Selecione as ofertas e clique em **Gerar Cenários**.")

st.markdown(f"""
    <hr style="border-top: 1px solid #E6E6E6; margin-top: 50px;">
    <p style="text-align: center; color: #888; font-size: 14px;">
        Desenvolvido por <b>Wanderson José</b> | 
        <a href="https://github.com/DevWandersonjose" target="_blank" style="color: #00A859; text-decoration: none;">GitHub</a><br>
        <i>Otimização de metas comerciais Stone - M1</i>
    </p>
""", unsafe_allow_html=True)
