import streamlit as st
import itertools
import pandas as pd
import io

st.set_page_config(layout="wide", page_title="Simulador M1", page_icon="🟩")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        color: #00A859 !important; 
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #00A859;'>🟩 Simulador de Metas - M1</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px; color: #555;'>Projete seu mix de clientes e maximize seus ganhos com inteligência.</p>", unsafe_allow_html=True)
st.divider()

DADOS_COMISSAO = {
    "10k (Mais Agressiva)":  {"valor": 90,  "tpv": 10000},
    "10k (Menos Agressiva)": {"valor": 50,  "tpv": 10000}, 
    "30k (Mais Agressiva)":  {"valor": 130, "tpv": 30000},
    "30k (Menos Agressiva)": {"valor": 100, "tpv": 30000}, 
    "50k (Mais Agressiva)":  {"valor": 260, "tpv": 50000},
    "50k (Menos Agressiva)": {"valor": 180, "tpv": 50000}, 
    "100k (Mais Agressiva)": {"valor": 340, "tpv": 100000},
    "100k (Menos Agressiva)":{"valor": 250, "tpv": 100000} 
}

def obter_multiplicador(tpv_total, meta_mes):
    if meta_mes == 0: return 1.0 
    
    atingimento = tpv_total / meta_mes
    if atingimento < 0.4: return 0.4
    if atingimento < 0.6: return 0.6
    if atingimento < 0.8: return 0.8
    if atingimento < 1.0: return 0.8  
    if atingimento < 1.2: return 1.2  
    if atingimento < 1.4: return 1.4
    if atingimento < 1.6: return 1.6
    if atingimento < 1.8: return 1.8
    return 2.0

def calcular_cenario(quantidades, meta_tpv):
    tpv_total = 0
    comissao_bruta = 0
    for tipo_cliente, qtd in quantidades.items():
        if tipo_cliente in DADOS_COMISSAO:
            tpv_total += qtd * DADOS_COMISSAO[tipo_cliente]["tpv"]
            comissao_bruta += qtd * DADOS_COMISSAO[tipo_cliente]["valor"]
            
    multiplicador = obter_multiplicador(tpv_total, meta_tpv)
    comissao_final = comissao_bruta * multiplicador
    return tpv_total, comissao_final, multiplicador

def simular_combinacoes(meta_dinheiro, limites_tpv, estrategia, meta_tpv):
    tipos_clientes = list(DADOS_COMISSAO.keys())
    ranges = []
    for tipo in tipos_clientes:
        if "10k" in tipo: ranges.append(range(limites_tpv["10k"] + 1))
        elif "30k" in tipo: ranges.append(range(limites_tpv["30k"] + 1))
        elif "50k" in tipo: ranges.append(range(limites_tpv["50k"] + 1))
        elif "100k" in tipo: ranges.append(range(limites_tpv["100k"] + 1))

    cenarios_encontrados = []

    for quantidades_tupla in itertools.product(*ranges):
        quantidades_dict = dict(zip(tipos_clientes, quantidades_tupla))
        
        limite_excedido = False
        categorias_tpv = ["10k", "30k", "50k", "100k"]
        for categoria in categorias_tpv:
            soma_categoria = sum(qtd for oferta, qtd in quantidades_dict.items() if oferta.startswith(categoria))
            if soma_categoria > limites_tpv[categoria]:
                limite_excedido = True
                break
                
        if limite_excedido:
            continue

        tpv, comissao, mult = calcular_cenario(quantidades_dict, meta_tpv)
        
        if comissao >= meta_dinheiro and comissao > 0:
            cenarios_encontrados.append({
                "mix": quantidades_dict,
                "tpv_total": tpv,
                "comissao_final": comissao,
                "multiplicador": mult,
                "total_clientes": sum(quantidades_dict.values())
            })
    
    if estrategia == "🎯 Menor Volume de TPV":
        cenarios_encontrados.sort(key=lambda x: (x['tpv_total'], x['total_clientes']))
    else:
        cenarios_encontrados.sort(key=lambda x: (x['total_clientes'], x['tpv_total']))
        
    return cenarios_encontrados

with st.sidebar:
    st.header("⚙️ Parâmetros da Simulação")
    
    meta_tpv_mes = st.number_input(
        "📈 Meta de TPV do Agente (R$)", min_value=0.0, value=300000.0, step=10000.0, format="%.2f"
    )
    meta_desejada = st.number_input(
        "💰 Meta de comissão no bolso (R$)", min_value=0.0, value=5000.0, step=500.0, format="%.2f"
    )
    
    st.markdown("---")
    
    estrategia_escolhida = st.radio(
        "🎯 Estratégia Principal", ["🎯 Menor Volume de TPV", "🚀 Menos Clientes (Multiplicador Alto)"]
    )
    
    st.markdown("---")
    st.subheader("⏱️ Limites Máximos por TPV")
    
    col_lim1, col_lim2 = st.columns(2)
    with col_lim1:
        lim_10k = st.number_input("Max 10k", min_value=0, max_value=10, value=3)
        lim_50k = st.number_input("Max 50k", min_value=0, max_value=5, value=2)
    with col_lim2:
        lim_30k = st.number_input("Max 30k", min_value=0, max_value=10, value=3)
        lim_100k = st.number_input("Max 100k", min_value=0, max_value=5, value=1)
        
    limites_tpv = {"10k": lim_10k, "30k": lim_30k, "50k": lim_50k, "100k": lim_100k}
    
    st.markdown("---")
    btn_simular = st.button("🚀 Gerar Cenários", use_container_width=True, type="primary")

if btn_simular:
    if meta_desejada > 0 and meta_tpv_mes > 0:
        with st.spinner("Analisando a matriz e calculando a melhor rota..."):
            cenarios = simular_combinacoes(meta_desejada, limites_tpv, estrategia_escolhida, meta_tpv_mes)
        
        if cenarios:
            st.toast("Simulação concluída com sucesso!", icon="✅")
            
            melhor_cenario = cenarios[0]
            mix_melhor_texto = " | ".join([f"{qtd}x {oferta}" for oferta, qtd in melhor_cenario['mix'].items() if qtd > 0])
            
            st.markdown("### 🏆 Melhor Cenário Sugerido")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Comissão Final", f"R$ {melhor_cenario['comissao_final']:,.2f}")
            col2.metric("TPV Total", f"R$ {melhor_cenario['tpv_total']:,.2f}")
            col3.metric("Multiplicador", f"{melhor_cenario['multiplicador']:.1f}x")
            col4.metric("Total de Clientes", melhor_cenario['total_clientes'])
            
            st.info(f"**Mix Ideal:** {mix_melhor_texto}")
            st.divider()
            
            st.markdown("### 📋 Outras Opções Viáveis")
            linhas_tabela = []
            
            for c in cenarios[1:51]: 
                linha = {}
                mix_texto = " | ".join([f"{qtd}x {oferta}" for oferta, qtd in c['mix'].items() if qtd > 0])
                linha["Mix Sugerido"] = mix_texto
                linha["Qtd Clientes"] = c['total_clientes']
                linha["TPV Total"] = f"R$ {c['tpv_total']:,.2f}"
                linha["Mult."] = f"{c['multiplicador']:.1f}x"
                linha["Comissão"] = f"R$ {c['comissao_final']:,.2f}"
                linhas_tabela.append(linha)
            
            st.dataframe(linhas_tabela, use_container_width=True)
            
            df_exportar = pd.DataFrame([{"Mix Sugerido": mix_melhor_texto, "Qtd Clientes": melhor_cenario['total_clientes'], "TPV Total": f"R$ {melhor_cenario['tpv_total']:,.2f}", "Mult.": f"{melhor_cenario['multiplicador']:.1f}x", "Comissão": f"R$ {melhor_cenario['comissao_final']:,.2f}"}] + linhas_tabela)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_exportar.to_excel(writer, index=False, sheet_name='Cenarios_M1')
            
            st.download_button(
                label="📥 Baixar Simulação em Excel",
                data=buffer.getvalue(),
                file_name="simulacao_M1_premium.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        else:
            st.warning("Nenhum cenário encontrado. Tente aumentar a quantidade máxima de clientes permitida no menu lateral.")
    else:
        st.error("As metas de comissão e de TPV devem ser maiores que zero.")
else:
    st.info("👈 Ajuste a sua meta e a quantidade de clientes no menu lateral e clique em **Gerar Cenários** para começar.")

st.markdown("""
    <hr style="border-top: 1px solid #E6E6E6; margin-top: 50px; margin-bottom: 20px;">
    <p style="text-align: center; color: #888888; font-size: 14px;">
        Desenvolvido por <b>Wanderson José</b> github.com/DevWandersonjose<br>
        <span style="font-size: 12px; color: #AAAAAA;">
            <i>Ferramenta de simulação criada para otimização de metas comerciais.</i>
        </span>
    </p>
""", unsafe_allow_html=True)