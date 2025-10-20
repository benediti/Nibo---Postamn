import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime
import sys, csv
import zipfile
import re

# Configuração da página
st.set_page_config(
    page_title="Nibo API - Gerador de Coleções Postman",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def validar_colunas_obrigatorias(df):
    """Valida se a planilha contém todas as colunas obrigatórias"""
    colunas_obrigatorias = [
        'stakeholderId', 'description', 'reference', 'date', 
        'Vencimento', 'categoryId', 'value', 'costCenterId'
    ]
    
    colunas_faltando = [col for col in colunas_obrigatorias if col not in df.columns]
    
    if colunas_faltando:
        st.error(f"❌ Colunas obrigatórias não encontradas: {', '.join(colunas_faltando)}")
        st.info("📋 Colunas obrigatórias:")
        for col in colunas_obrigatorias:
            st.text(f"  • {col}")
        return False
    
    return True

def validar_dados(df):
    """Valida os dados da planilha"""
    erros = []
    
    # Verificar se há linhas vazias
    linhas_vazias = df.isnull().all(axis=1).sum()
    if linhas_vazias > 0:
        erros.append(f"🔍 {linhas_vazias} linha(s) completamente vazia(s) encontrada(s)")
    
    # Verificar valores monetários
    try:
        pd.to_numeric(df['value'], errors='coerce')
    except:
        erros.append("💰 Coluna 'value' contém valores não numéricos")
    
    # Verificar datas
    valores_nulos = df[['stakeholderId', 'description', 'date', 'Vencimento']].isnull().sum()
    for coluna, nulos in valores_nulos.items():
        if nulos > 0:
            erros.append(f"📅 {nulos} valor(es) nulo(s) na coluna '{coluna}'")
    
    return erros

def _safe_filename(s: str) -> str:
    s = str(s or "").strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '_', s)
    return (s or "item")[:80]

def converter_planilha_para_json(df, token_api, nome_colecao):
    """Converte a planilha em formato JSON para coleção Postman"""
    json_list = []
    
    for _, row in df.iterrows():
        # Pular linhas completamente vazias
        if pd.isna(row).all():
            continue
            
        json_data = {
            "stakeholderId": str(row["stakeholderId"]) if pd.notna(row["stakeholderId"]) else "",
            "description": str(row["description"]) if pd.notna(row["description"]) else "",
            "reference": str(row["reference"]) if pd.notna(row["reference"]) else "",
            "scheduleDate": str(row["date"]) if pd.notna(row["date"]) else "",
            "dueDate": str(row["Vencimento"]) if pd.notna(row["Vencimento"]) else "",
            "accrualDate": str(row["date"]) if pd.notna(row["date"]) else "",
            "categories": [
                {
                    "categoryId": str(row["categoryId"]) if pd.notna(row["categoryId"]) else "",
                    "value": float(row["value"]) if pd.notna(row["value"]) else 0.0
                }
            ],
            "costCenterValueType": 0,
            "costCenters": [
                {
                    "costCenterId": str(row["costCenterId"]) if pd.notna(row["costCenterId"]) else "",
                    "value": float(row["value"]) if pd.notna(row["value"]) else 0.0
                }
            ]
        }
        json_list.append(json_data)
    
    # Criar coleção Postman
    colecao_postman = {
        "info": {
            "name": nome_colecao,
            "_postman_id": f"auto-generated-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": f"Coleção gerada automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        },
        "item": []
    }
    
    for i, item in enumerate(json_list):
        colecao_postman["item"].append({
            "name": f"Agendamento {i+1} - {item['description'][:50]}{'...' if len(item['description']) > 50 else ''}",
            "request": {
                "method": "POST",
                "header": [
                    {"key": "Content-Type", "value": "application/json"},
                    {"key": "ApiToken", "value": f"{token_api}"}
                ],
                "url": {
                    "raw": "https://api.nibo.com.br/empresas/v1/schedules/debit",
                    "protocol": "https",
                    "host": ["api", "nibo", "com", "br"],
                    "path": ["empresas", "v1", "schedules", "debit"]
                },
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(item, indent=2, ensure_ascii=False)
                }
            },
            "response": []
        })
    
    return colecao_postman, len(json_list), json_list

def criar_colecao_com_runner(df, token_api, nome_colecao):
    """Cria coleção otimizada para Collection Runner com arquivo de dados"""
    json_list = []
    data_file_list = []
    
    for i, row in df.iterrows():
        # Pular linhas completamente vazias
        if pd.isna(row).all():
            continue
            
        json_data = {
            "stakeholderId": str(row["stakeholderId"]) if pd.notna(row["stakeholderId"]) else "",
            "description": str(row["description"]) if pd.notna(row["description"]) else "",
            "reference": str(row["reference"]) if pd.notna(row["reference"]) else "",
            "scheduleDate": str(row["date"]) if pd.notna(row["date"]) else "",
            "dueDate": str(row["Vencimento"]) if pd.notna(row["Vencimento"]) else "",
            "accrualDate": str(row["date"]) if pd.notna(row["date"]) else "",
            "categories": [
                {
                    "categoryId": str(row["categoryId"]) if pd.notna(row["categoryId"]) else "",
                    "value": float(row["value"]) if pd.notna(row["value"]) else 0.0
                }
            ],
            "costCenterValueType": 0,
            "costCenters": [
                {
                    "costCenterId": str(row["costCenterId"]) if pd.notna(row["costCenterId"]) else "",
                    "value": float(row["value"]) if pd.notna(row["value"]) else 0.0
                }
            ]
        }
        
        json_list.append(json_data)
        # Arquivo de dados para o Runner
        data_file_list.append({
            "requestData": json.dumps(json_data, ensure_ascii=False),
            "description": json_data["description"]
        })
    
    # Coleção otimizada com Pre-request Script
    pre_request_script = '''
// Script para carregar dados dinamicamente no Collection Runner
const requestData = pm.iterationData.get("requestData");

if (requestData) {
    // Define o body da requisição com os dados da iteração atual
    pm.request.body.raw = requestData;
    
    // Log para debug
    console.log("Enviando dados:", JSON.parse(requestData).description);
}
'''
    
    colecao_runner = {
        "info": {
            "name": f"{nome_colecao} - Collection Runner",
            "_postman_id": f"runner-generated-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": f"Coleção otimizada para Collection Runner - {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        },
        "item": [
            {
                "name": "Criar Agendamento Nibo",
                "event": [
                    {
                        "listen": "prerequest",
                        "script": {
                            "exec": pre_request_script.split('\n'),
                            "type": "text/javascript"
                        }
                    }
                ],
                "request": {
                    "method": "POST",
                    "header": [
                        {"key": "Content-Type", "value": "application/json"},
                        {"key": "ApiToken", "value": f"{token_api}"}
                    ],
                    "url": {
                        "raw": "https://api.nibo.com.br/empresas/v1/schedules/debit",
                        "protocol": "https",
                        "host": ["api", "nibo", "com", "br"],
                        "path": ["empresas", "v1", "schedules", "debit"]
                    },
                    "body": {
                        "mode": "raw",
                        "raw": "// Este body será substituído pelo Pre-request Script"
                    }
                },
                "response": []
            }
        ]
    }
    
    return colecao_runner, data_file_list, len(json_list)

# Função para corrigir arquivos CSV com problemas de codificação
def corrigir_csv(inp):
    """
    inp: UploadedFile (Streamlit) ou caminho (str)
    Retorna: io.StringIO com CSV corrigido pronto para pd.read_csv
    """
    # Ler conteúdo como texto
    if hasattr(inp, "read"):
        raw = inp.read()
        text = raw.decode('utf-8', errors='replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
    else:
        with open(inp, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    
    lines = text.splitlines()
    if not lines:
        return io.StringIO("")
    
    header = lines[0].rstrip('\n')
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header.split(','))
    for line in lines[1:]:
        line = line.rstrip('\n')
        if not line.strip():
            continue
        # tenta localizar o JSON no começo, testando prefixos até json.loads funcionar
        j = None
        for i in range(1, len(line)+1):
            try:
                candidate = line[:i]
                json.loads(candidate)
                j = candidate
                rest = line[i+1:] if i < len(line) and i < len(line) and line[i] == ',' else line[i:]
                writer.writerow([j, rest])
                break
            except Exception:
                continue
        if j is None:
            # fallback: grava toda a linha em uma coluna
            writer.writerow([line])
    output.seek(0)
    return output

def criar_zip_jsons(json_list):
    """Recebe lista de objetos JSON e retorna bytes do ZIP com cada objeto em um arquivo separado"""
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i, obj in enumerate(json_list, start=1):
            name_safe = _safe_filename(obj.get("description", f"item_{i}"))
            filename = f"{i:03d}_{name_safe}.json"
            content = json.dumps(obj, indent=2, ensure_ascii=False)
            zf.writestr(filename, content)
    mem_zip.seek(0)
    return mem_zip.getvalue()

# Interface principal
st.title("💰 Nibo API - Gerador de Coleções Postman")
st.markdown("---")

st.markdown("""
### 📋 Como usar:
1. **Configure** seu token da API Nibo na barra lateral
2. **Carregue** sua planilha Excel/CSV com os dados financeiros
3. **Gere** a coleção Postman automaticamente
4. **Baixe** o arquivo JSON para importar no Postman ou um ZIP com um JSON por linha
""")

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Token da API
    token_api = st.text_input(
        "🔑 Token da API Nibo:",
        type="password",
        help="Será enviado no header 'ApiToken' (não use Authorization)"
    )
    
    # Nome da coleção
    nome_colecao = st.text_input(
        "📝 Nome da Coleção:",
        value="Nibo Agendamentos Automáticos",
        help="Nome que aparecerá na coleção do Postman"
    )
    
    st.markdown("---")
    st.markdown("### 📊 Colunas Obrigatórias:")
    colunas_obrigatorias = [
        'stakeholderId', 'description', 'reference', 'date', 
        'Vencimento', 'categoryId', 'value', 'costCenterId'
    ]
    for col in colunas_obrigatorias:
        st.text(f"• {col}")

# Área principal para upload de arquivo
st.header("📁 Upload da Planilha")

uploaded_file = st.file_uploader(
    "Escolha sua planilha:",
    type=['xlsx', 'xls', 'csv'],
    help="Formatos aceitos: Excel (.xlsx, .xls) ou CSV (.csv)"
)

if uploaded_file is not None:
    try:
        # Ler o arquivo
        if uploaded_file.name.endswith('.csv'):
            # Corrigir o CSV (UploadedFile -> StringIO)
            arquivo_corrigido_io = corrigir_csv(uploaded_file)
            df = pd.read_csv(arquivo_corrigido_io)
            st.success("✅ Arquivo CSV corrigido e carregado com sucesso!")
        else:
            df = pd.read_excel(uploaded_file)
            st.success(f"✅ Arquivo Excel carregado com sucesso! {len(df)} linha(s) encontrada(s)")
        
        # Mostrar preview dos dados
        with st.expander("👁️ Preview dos Dados", expanded=True):
            st.dataframe(df.head(10), use_container_width=True)
            if len(df) > 10:
                st.info(f"Mostrando as primeiras 10 linhas de {len(df)} total")
        
        # Validar colunas obrigatórias
        if validar_colunas_obrigatorias(df):
            st.success("✅ Todas as colunas obrigatórias encontradas!")
            
            # Validar dados
            erros = validar_dados(df)
            if erros:
                with st.expander("⚠️ Avisos de Validação", expanded=True):
                    for erro in erros:
                        st.warning(erro)
            
            # Estatísticas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total de Linhas", len(df))
            with col2:
                st.metric("💰 Valor Total", f"R$ {df['value'].sum():,.2f}")
            with col3:
                st.metric("🏢 Stakeholders Únicos", df['stakeholderId'].nunique())
            with col4:
                st.metric("🏷️ Categorias Únicas", df['categoryId'].nunique())
            
            # Opções de geração
            st.markdown("---")
            st.subheader("🚀 Gerar Coleção Postman")
            
            tipo_colecao = st.radio(
                "Escolha o tipo de coleção:",
                ["📋 Coleção Tradicional", "⚡ Coleção para Collection Runner"],
                help="Tradicional: Uma requisição por linha da planilha\nCollection Runner: Uma requisição única que usa dados externos"
            )
            
            # Botão para gerar coleção
            if st.button("🚀 Gerar Coleção", type="primary", use_container_width=True):
                if not token_api:
                    st.error("❌ Por favor, insira o token da API Nibo na barra lateral (header ApiToken)")
                elif not nome_colecao:
                    st.error("❌ Por favor, insira um nome para a coleção")
                else:
                    with st.spinner("🔄 Gerando coleção Postman..."):
                        if tipo_colecao == "📋 Coleção Tradicional":
                            # Coleção tradicional
                            colecao, total_requests, json_list = converter_planilha_para_json(df, token_api, nome_colecao)
                            
                            json_string = json.dumps(colecao, indent=2, ensure_ascii=False)
                            
                            st.success(f"✅ Coleção tradicional gerada! {total_requests} requisições criadas")
                            
                            # Botão de download da coleção
                            st.download_button(
                                label="📥 Baixar Coleção Postman",
                                data=json_string,
                                file_name=f"nibo_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )

                            # ZIP com um JSON por linha
                            zip_bytes = criar_zip_jsons(json_list)
                            st.download_button(
                                label="📥 Baixar JSONs por linha (ZIP)",
                                data=zip_bytes,
                                file_name=f"nibo_jsons_por_linha_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                            
                        else:
                            # Coleção para Collection Runner
                            colecao_runner, data_file, total_requests = criar_colecao_com_runner(df, token_api, nome_colecao)
                            
                            # Criar arquivo de dados CSV para o runner
                            df_runner = pd.DataFrame(data_file)
                            csv_data = df_runner.to_csv(index=False, encoding='utf-8')
                            
                            json_string = json.dumps(colecao_runner, indent=2, ensure_ascii=False)
                            
                            st.success(f"✅ Coleção para Runner gerada! {total_requests} registros preparados")
                            
                            # Downloads
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    label="📥 Baixar Coleção",
                                    data=json_string,
                                    file_name=f"nibo_runner_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                    mime="application/json",
                                    use_container_width=True
                                )
                            with col2:
                                st.download_button(
                                    label="📊 Baixar Dados CSV",
                                    data=csv_data,
                                    file_name=f"nibo_runner_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )

                            # Também ZIP com JSONs do runner
                            zip_bytes = criar_zip_jsons([json.loads(d["requestData"]) for d in data_file])
                            st.download_button(
                                label="📥 Baixar JSONs por linha (ZIP)",
                                data=zip_bytes,
                                file_name=f"nibo_jsons_por_linha_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                        
                        # Mostrar preview da coleção
                        with st.expander("🔍 Preview da Coleção JSON"):
                            if tipo_colecao == "📋 Coleção Tradicional":
                                st.json(colecao, expanded=False)
                            else:
                                st.json(colecao_runner, expanded=False)
    
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        st.info("💡 Verifique se o arquivo está no formato correto e não está corrompido")

else:
    st.info("👆 Faça upload de uma planilha para começar")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "💡 <strong>Dica:</strong> Use o header ApiToken e o endpoint https://api.nibo.com.br/empresas/v1/schedules/debit"
    "</div>",
    unsafe_allow_html=True
)
