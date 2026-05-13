import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import scraper_atacadao
import scraper_tenda

st.set_page_config(page_title="Price Tracker - UNIVESP", layout="wide")
st.title("📊 Price Tracker: Monitoramento de Preços - Supermercados")

# O decorador faz o Streamlit guardar os dados em cache por 60 segundos
@st.cache_data(ttl=60) 
def carregar_produtos():
    try:
        conn = sqlite3.connect("pricetracker.db") 
        query = "SELECT id, nome FROM produtos" 
        df = pd.read_sql(query, conn)
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Erro ao conectar no banco de dados: {e}")
        return []

@st.cache_data(ttl=60) 
def carregar_precos(produto_id):
    try:
        conn = sqlite3.connect("pricetracker.db") 
        query = """
        SELECT rp.*, p.nome as produto_nome, e.nome as estabelecimento 
        FROM registros_precos rp 
        JOIN produtos p ON rp.produto_id = p.id 
        JOIN estabelecimentos e ON rp.estabelecimento_id = e.id 
        WHERE rp.produto_id = ?
        """
        df = pd.read_sql(query, conn, params=(produto_id,))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no banco de dados: {e}")
        return pd.DataFrame()

# Sidebar
st.sidebar.header("⚙️ Opções")
if st.sidebar.button("🔄 Atualizar Dados"):
    st.rerun()

if st.sidebar.button('Atualizar Preços Agora'):
    with st.spinner('Coletando dados... Isso pode levar um minuto.'):
        scraper_atacadao.buscar_atacadao("arroz", 1) 
        scraper_tenda.buscar_tenda()
        
        # Limpa o cache para forçar a leitura dos novos dados do banco
        st.cache_data.clear() 
        
        st.success('Dados atualizados com sucesso!')
        # A página vai recarregar automaticamente e mostrar os dados novos

try:
    # 1. Carregar Produtos
    produtos = carregar_produtos()

    if not produtos:
        st.error("❌ Nenhum produto encontrado. Rode o seed.py.")
        st.stop()

    nomes_produtos = {p['nome']: p['id'] for p in produtos}
    label = st.sidebar.selectbox("🛒 Selecione a Categoria:", list(nomes_produtos.keys()))
    produto_id = nomes_produtos[label]

    # 2. Carregar Preços
    df = carregar_precos(produto_id)

    if df.empty:
        st.warning(f"⚠️ Nenhum dado encontrado para '{label}'. Rode o scraper.")
        st.stop()
    
    if not df.empty:
        # 1. Tratamento de Tipos (Essencial para não quebrar gráficos)
        df['preco'] = pd.to_numeric(df['preco'], errors='coerce').astype(float)
        
        # 2. Tratamento de Datas (Conversão segura para histórico)
        # Se a data vier como string da API, convertemos para objeto datetime primeiro
        df['data_coleta'] = pd.to_datetime(df['data_coleta'], errors='coerce')
        
        # 3. Ordenação por Data (Garante que o gráfico de histórico faça sentido)
        df = df.sort_values("data_coleta", ascending=False)
        
        # 4. Formatação para exibição na tabela (Cria uma cópia legível)
        df['data_formatada'] = df['data_coleta'].dt.strftime('%d/%m/%Y %H:%M')
        
        # 5. Tratamento de Nulos
        df['nome_detalhado'] = df['nome_detalhado'].fillna("Produto sem nome")
        df['imagem_url'] = df['imagem_url'].fillna("https://placehold.co/200x200")
        
        st.success(f"✅ Exibindo {len(df)} coletas encontradas para '{label}'.")
    else:
        st.warning(f"⚠️ O banco retornou uma lista vazia para '{label}'. Verifique se o Scraper salvou os dados com o ID correto.")
        st.stop()
    # 4. Métricas
    st.subheader(f"📦 Categoria: {label}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Menor Preço",   f"R$ {df['preco'].min():.2f}")
    c2.metric("📈 Maior Preço",   f"R$ {df['preco'].max():.2f}")
    c3.metric("📊 Preço Médio",   f"R$ {df['preco'].mean():.2f}")
    c4.metric("🔢 Total Coletas", len(df))

# 5. VITRINE DE PRODUTOS COM IMAGENS
    st.write("### 🖼️ Vitrine de Produtos")
    cols = st.columns(5)
    
    # Isola o DataFrame limpo com os top 10 produtos
    top_produtos = df.drop_duplicates("nome_detalhado").head(10)
    
    # O uso do 'enumerate' cria um contador (0, 1, 2...) independente do índice do Pandas (idx_pandas)
    for contador, (idx_pandas, row) in enumerate(top_produtos.iterrows()):
        with cols[contador % 5]:
            if row['imagem_url']:
                st.image(row['imagem_url'], use_container_width=True)
            else:
                st.image("https://placehold.co/200x200", use_container_width=True)
            st.caption(f"**{row['nome_detalhado'][:35]}**")
            st.write(f"💰 R$ {row['preco']:.2f}")

    st.divider()

# 5.5 Gráfico de Evolução de Preços no Tempo (O Comparador)
    st.write("### 📈 Evolução Histórica de Preços")
    
    # Para o gráfico de linhas não ligar os pontos de trás pra frente, precisamos ordenar a data do mais antigo para o mais novo
    df_tempo = df.sort_values("data_coleta")
    
    fig_linha = px.line(
        df_tempo, 
        x="data_coleta", 
        y="preco", 
        color="estabelecimento", #  Uma cor para cada loja
        hover_name="nome_detalhado", # Mostra o nome da marca ao passar o mouse
        markers=True,
        title=f"Comparativo de Preços ao Longo do Tempo — {label}",
        labels={"data_coleta": "Data da Coleta", "preco": "Preço (R$)", "estabelecimento": "Supermercado"}
    )
    st.plotly_chart(fig_linha, use_container_width=True)

# 6. Gráfico de Barras por Marca
    st.write("### 🏷️ Preço por Marca")
    fig_barras = px.bar(
        df.sort_values("preco"),
        x="nome_detalhado",
        y="preco",
        # Alterei para color_discrete_sequence para evitar o gradiente se preferir algo mais limpo,
        # mas mantive a lógica de cor baseada no preço para destaque.
        color="preco", 
        color_continuous_scale="Teal",
        title=f"Comparativo de Preços por Marca — {label}",
        labels={"nome_detalhado": "Produto/Marca", "preco": "Preço (R$)"}
    )
    # Melhorei o ângulo e o espaçamento do layout
    fig_barras.update_layout(
        xaxis_tickangle=-45,
        bargap=0.3, # Adiciona espaço entre as marcas
        margin=dict(b=100) # Espaço extra embaixo para nomes longos não cortarem
    )
    st.plotly_chart(fig_barras, use_container_width=True)

    # 7. Distribuição dos Preços (Histograma)
    st.write("### 📉 Distribuição dos Preços")
    fig_hist = px.histogram(
        df, 
        x="preco", 
        nbins=15, # Aumentei os bins para maior granularidade
        title="Distribuição dos Preços Coletados",
        labels={"preco": "Preço (R$)"},
        color_discrete_sequence=["#636EFA"],
        # Adiciona bordas nas barras para separá-las visualmente
    )
    
    # O SEGREDO DO ESPAÇO: update_layout com bargap
    fig_hist.update_layout(
        bargap=0.1, # Espaço entre as barras do histograma
        xaxis_title="Faixa de Preço (R$)",
        yaxis_title="Quantidade de Produtos",
        plot_bgcolor="rgba(0,0,0,0)" # Fundo limpo
    )
    
    # Adiciona linhas de grade suaves
    fig_hist.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    st.plotly_chart(fig_hist, use_container_width=True)

    # 8. Tabela Detalhada
    st.write("### 📋 Tabela Completa")
    st.dataframe(
        df[["nome_detalhado", "estabelecimento", "preco", "data_coleta", "em_promocao"]].rename(columns={
            "nome_detalhado":  "Produto/Marca",
            "estabelecimento": "Loja",
            "preco":           "Preço (R$)",
            "data_coleta":     "Data",
            "em_promocao":     "Em Promoção"
        }),
        use_container_width=True
    )

except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {e}")