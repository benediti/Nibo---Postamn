import streamlit as st
import pandas as pd
import json
import io
import zipfile
from datetime import datetime

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
            "description": f"Coleção gerada automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\nEndpoint: https://api.nibo.com.br/empresas/v1/schedules/debit"
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
                    {"key": "ApiToken", "value": token_api, "type": "text"}
                ],
                "url": {
                    "raw": "https://api.nibo.com.br/empresas/v1/schedules/debit",
                    "protocol": "https",
                    "host": ["api", "nibo", "com", "br"],
                    "path": ["empresas", "v1", "schedules", "debit"]
                },
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(item, indent=2, ensure_ascii=False),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            },
            "response": []
        })
    
    return colecao_postman, len(json_list), json_list

def criar_jsons_individuais(df):
    """Cria JSONs individuais para cada linha da planilha"""
    json_list = []
    
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
    
    return json_list

def criar_zip_com_jsons(json_list):
    """Cria arquivo ZIP com JSONs individuais"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Criar arquivo de controle para Collection Runner
        control_data = []
        
        for i, json_data in enumerate(json_list):
            # Nome do arquivo baseado na descrição
            descricao_limpa = "".join(c for c in json_data["description"] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            nome_arquivo = f"agendamento_{i+1:03d}_{descricao_limpa[:30]}.json"
            
            # Adicionar JSON individual ao ZIP
            json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
            zip_file.writestr(nome_arquivo, json_string)
            
            # Adicionar ao arquivo de controle
            control_data.append({"file": nome_arquivo})
        
        # Criar arquivo de controle data.json
        control_json = json.dumps(control_data, indent=2, ensure_ascii=False)
        zip_file.writestr("data.json", control_json)
        
        # Criar arquivo README com instruções
        readme_content = f"""# Nibo API - JSONs Individuais
Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

## ⚠️ IMPORTANTE - API Nibo usa ApiToken no Header

**CORRETO**: ApiToken: SEU_TOKEN_AQUI
**ERRADO**: Authorization: Bearer SEU_TOKEN_AQUI

## Endpoint da API:
```
POST https://api.nibo.com.br/empresas/v1/schedules/debit
```

## Headers necessários:
```
Content-Type: application/json
ApiToken: SEU_TOKEN_AQUI
```

## Arquivos inclusos:
- {len(json_list)} arquivos JSON individuais (agendamento_XXX_*.json)
- data.json: Arquivo de controle para Collection Runner do Postman

## Como usar no Postman Collection Runner:

### Método 1 - Collection Runner com arquivos locais (Recomendado)

1. **Crie uma requisição POST** para: 
   ```
   https://api.nibo.com.br/empresas/v1/schedules/debit
   ```

2. **Adicione os headers**:
   - Content-Type: application/json
   - ApiToken: SEU_TOKEN_AQUI

3. **Pre-request Script** (copie e cole):
```javascript
const fs = require('fs');
const path = require('path');

// Caminho onde você extraiu os JSONs - AJUSTE ESTE CAMINHO!
const basePath = "C:/caminho/para/seus/jsons";

// Obtém o nome do arquivo da variável "file"
const fileName = pm.iterationData.get("file");
const filePath = path.join(basePath, fileName);

try {{
    // Lê o conteúdo do JSON e define como body
    const fileContent = fs.readFileSync(filePath, 'utf8');
    pm.request.body.raw = fileContent;
    
    console.log("✅ Carregando arquivo:", fileName);
    console.log("Descrição:", JSON.parse(fileContent).description);
}} catch (error) {{
    console.error("❌ Erro ao carregar arquivo:", error);
}}
```

4. **No Collection Runner**:
   - Selecione sua coleção
   - Clique em "Select File" na seção Data
   - Escolha o arquivo **data.json**
   - Configure iterações: {len(json_list)}
   - Ajuste o delay entre requisições (recomendado: 500ms)
   - Clique em "Run"

### Método 2 - Uso Manual (para testes)

1. Abra qualquer arquivo JSON individual
2. Copie o conteúdo
3. Cole no body da requisição POST no Postman
4. Adicione os headers mencionados acima
5. Execute a requisição

## Estrutura dos arquivos:
Cada JSON contém um agendamento completo com:
- stakeholderId, description, reference
- scheduleDate, dueDate, accrualDate
- categories (categoryId + value)
- costCenters (costCenterId + value)
- costCenterValueType: 0 (fixo)

## Troubleshooting:

### Erro "Cannot read property of undefined"
- Verifique se o caminho no Pre-request Script está correto
- Confirme que todos os arquivos JSON estão na pasta especificada

### Erro 401 - Unauthorized
- Verifique se está usando "ApiToken" no header (não "Authorization")
- Confirme se o token está correto e ativo

### Erro 400 - Bad Request
- Verifique se os IDs (stakeholderId, categoryId, costCenterId) existem no Nibo
- Confirme se as datas estão no formato correto

## Dicas:
- Configure um delay de 500-1000ms entre requisições para evitar sobrecarga
- Use o Console do Postman para debug (View > Show Postman Console)
- Teste com 1-2 requisições antes de executar todas
- Salve os logs do Runner para análise posterior
"""
        zip_file.writestr("README.md", readme_content)
    
    zip_buffer.seek(0)
    return zip_buffer

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
    pre_request_script = '''// Script para carregar dados dinamicamente no Collection Runner
const requestData = pm.iterationData.get("requestData");

if (requestData) {
    // Define o body da requisição com os dados da iteração atual
    pm.request.body.raw = requestData;
    
    // Log para debug
    const data = JSON.parse(requestData);
    console.log("✅ Enviando agendamento:", data.description);
    console.log("Valor:", data.categories[0].value);
} else {
    console.error("❌ Dados não encontrados para esta iteração");
}'''
    
    test_script = '''// Test Script para validar a resposta
pm.test("Status code é 200 ou 201", function () {
    pm.expect(pm.response.code).to.be.oneOf([200, 201]);
});

pm.test("Resposta não contém erro", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.error).to.be.undefined;
});

// Log da resposta
console.log("Resposta:", pm.response.json());'''
    
    colecao_runner = {
        "info": {
            "name": f"{nome_colecao} - Collection Runner",
            "_postman_id": f"runner-generated-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": f"Coleção otimizada para Collection Runner - {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\n⚠️ IMPORTANTE: Use 'ApiToken' no header, não 'Authorization'\n\nEndpoint: https://api.nibo.com.br/empresas/v1/schedules/debit"
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
                    },
                    {
                        "listen": "test",
                        "script": {
                            "exec": test_script.split('\n'),
                            "type": "text/javascript"
                        }
                    }
                ],
                "request": {
                    "method": "POST",
                    "header": [
                        {"key": "Content-Type", "value": "application/json", "type": "text"},
                        {"key": "ApiToken", "value": token_api, "type": "text"}
                    ],
                    "url": {
                        "raw": "https://api.nibo.com.br/empresas/v1/schedules/debit",
                        "protocol": "https",
                        "host": ["api", "nibo", "com", "br"],
                        "path": ["empresas", "v1", "schedules", "debit"]
                    },
                    "body": {
                        "mode": "raw",
                        "raw": "// Este body será substituído pelo Pre-request Script\n{\n  \"stakeholderId\": \"\",\n  \"description\": \"\"\n}",
                        "options": {
                            "raw": {
                                "language": "json"
                            }
                        }
                    }
                },
                "response": []
            }
        ]
    }
    
    return colecao_runner, data_file_list, len(json_list)

# Interface principal
st.title("💰 Nibo API - Gerador de Coleções Postman")
st.markdown("---")

# Alerta importante sobre o token
st.warning("⚠️ **IMPORTANTE**: A API do Nibo usa `ApiToken` no header, NÃO use `Authorization: Bearer`")

st.markdown("""
### 📋 Como usar:
1. **Configure** seu token da API Nibo na barra lateral
2. **Carregue** sua planilha Excel/CSV com os dados financeiros
3. **Gere** a coleção Postman automaticamente
4. **Baixe** o arquivo JSON para importar no Postman
5. **Execute** no Collection Runner do Postman

### 🔑 Endpoint da API:
```
POST https://api.nibo.com.br/empresas/v1/schedules/debit
```

### 📦 Headers necessários:
```
Content-Type: application/json
ApiToken: SEU_TOKEN_AQUI
```
""")

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Token da API
    st.info("💡 **Dica**: O Nibo usa `ApiToken` no header")
    token_api = st.text_input(
        "🔑 Token da API Nibo:",
        type="password",
        help="Insira seu token de autenticação da API Nibo (será usado no header ApiToken)"
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
    
    st.markdown("---")
    st.markdown("### 🔗 Links Úteis:")
    st.markdown("[📚 Documentação Nibo](https://api.nibo.com.br)")
    st.markdown("[📮 Postman Download](https://www.postman.com/downloads/)")

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
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ Arquivo carregado com sucesso! {len(df)} linha(s) encontrada(s)")
        
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
                ["⚡ Coleção para Collection Runner (Recomendado)", "📋 Coleção Tradicional", "📁 JSONs Individuais (ZIP)"],
                help="**Collection Runner**: Mais eficiente, uma requisição com dados externos (CSV)\n\n**Tradicional**: Uma requisição separada por linha da planilha\n\n**JSONs Individuais**: Cada linha vira um arquivo JSON separado com opção de uso no Runner"
            )
            
            # Botão para gerar coleção
            if st.button("🚀 Gerar Coleção", type="primary", use_container_width=True):
                if not token_api:
                    st.error("❌ Por favor, insira o token da API Nibo na barra lateral")
                elif not nome_colecao:
                    st.error("❌ Por favor, insira um nome para a coleção")
                else:
                    with st.spinner("🔄 Gerando coleção Postman..."):
                        if tipo_colecao == "📋 Coleção Tradicional":
                            # Coleção tradicional
                            colecao, total_requests, _ = converter_planilha_para_json(df, token_api, nome_colecao)
                            
                            json_string = json.dumps(colecao, indent=2, ensure_ascii=False)
                            
                            st.success(f"✅ Coleção tradicional gerada! {total_requests} requisições criadas")
                            
                            st.info("💡 **Uso**: Importe no Postman e execute cada requisição individualmente ou use 'Run Collection'")
                            
                            # Botão de download
                            st.download_button(
                                label="📥 Baixar Coleção Postman",
                                data=json_string,
                                file_name=f"nibo_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                            
                        elif tipo_colecao == "⚡ Coleção para Collection Runner (Recomendado)":
                            # Coleção para Collection Runner
                            colecao_runner, data_file, total_requests = criar_colecao_com_runner(df, token_api, nome_colecao)
                            
                            # Criar arquivo de dados CSV para o runner
                            df_runner = pd.DataFrame(data_file)
                            csv_data = df_runner.to_csv(index=False, encoding='utf-8-sig')
                            
                            json_string = json.dumps(colecao_runner, indent=2, ensure_ascii=False)
                            
                            st.success(f"✅ Coleção para Runner gerada! {total_requests} registros preparados")
                            
                            # Downloads
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    label="📥 1️⃣ Baixar Coleção JSON",
                                    data=json_string,
                                    file_name=f"nibo_runner_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                    mime="application/json",
                                    use_container_width=True
                                )
                            with col2:
                                st.download_button(
                                    label="📊 2️⃣ Baixar Dados CSV",
                                    data=csv_data,
                                    file_name=f"nibo_runner_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                            
                            # Instruções de uso
                            with st.expander("📖 Como usar no Collection Runner", expanded=True):
                                st.markdown("""
                                ### 🎯 Passo a passo:
                                
                                1. **Baixe os 2 arquivos** acima (JSON e CSV)
                                2. **Importe a coleção JSON** no Postman
                                3. **Abra a coleção** e clique em "Run" (ícone de play)
                                4. **Na aba "Data"**: Clique em "Select File" e escolha o arquivo CSV
                                5. **Configure**:
                                   - Iterations: Automático (baseado no CSV)
                                   - Delay: 500ms (recomendado)
                                6. **Clique em "Run"** e acompanhe o progresso!
                                
                                ### ⚡ Vantagens do Collection Runner:
                                - ✅ **Mais eficiente** - Uma requisição configurável para todos os dados
                                - ✅ **Controle de velocidade** - Delay entre requisições evita sobrecarga
                                - ✅ **Relatórios detalhados** - Veja sucessos/falhas em tempo real
                                - ✅ **Logs completos** - Debug facilitado no Console
                                - ✅ **Testes automáticos** - Validação de status code e resposta
                                
                                ### 🐛 Debug:
                                - Abra o Postman Console (View > Show Postman Console)
                                - Veja os logs de cada requisição em tempo real
                                - Identifique facilmente quais agendamentos falharam
                                """)
                        
                        else:
                            # JSONs Individuais em ZIP
                            json_list = criar_jsons_individuais(df)
                            zip_data = criar_zip_com_jsons(json_list)
                            
                            st.success(f"✅ ZIP com JSONs individuais gerado! {len(json_list)} arquivos criados")
                            
                            # Download do ZIP
                            st.download_button(
                                label="📦 Baixar ZIP com JSONs Individuais",
                                data=zip_data.getvalue(),
                                file_name=f"nibo_jsons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                            
                            # Instruções de uso
                            with st.expander("📖 Como usar os JSONs individuais", expanded=True):
                                st.markdown(f"""
                                ### 📦 Conteúdo do ZIP:
                                - **{len(json_list)} arquivos JSON** individuais (um por agendamento)
                                - **data.json**: Arquivo de controle para Collection Runner
                                - **README.md**: Instruções detalhadas de uso
                                
                                ### 🔧 Opção 1 - Collection Runner (
