import pdfplumber
import json
import re
import os
import argparse

def extract_sped_layout(pdf_path, output_json):
    """
    Função heurística para extrair a estrutura de blocos e registros 
    dos Manuais do SPED (ECD/ECF).
    """
    print(f"Lendo o manual: {pdf_path}")
    
    # Dicionário para armazenar o mapeamento de Registros
    # Ex: "I200": {"descricao": "Lançamento Contábil", "nivel": 2, "ocorrencia": "1:N"}
    registros = {}
    
    # Regex para capturar os títulos de registros no padrão do Manual
    # Ex: "Registro I200: Lançamento Contábil" ou "Registro I250 – Partidas do Lançamento"
    regex_registro = re.compile(r'Registro\s+([A-Z0-9]{4})[\s:–-]+(.+)', re.IGNORECASE)
    
    # Regex para capturar o Nível Hierárquico e Ocorrência nas tabelas (simplificado)
    # Normalmente essas informações estão no texto logo abaixo do título do registro
    regex_nivel = re.compile(r'Nível\s*hierárquico\s*:\s*(\d+)', re.IGNORECASE)
    regex_ocorrencia = re.compile(r'Ocorrência\s*:\s*([^ \n]+)', re.IGNORECASE)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_paginas = len(pdf.pages)
            print(f"Total de páginas: {total_paginas}. Extraindo texto, isso pode demorar alguns minutos...")
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                linhas = text.split('\n')
                ultimo_registro = None
                
                for linha in linhas:
                    # Tentar encontrar um novo registro
                    match_reg = regex_registro.match(linha.strip())
                    if match_reg:
                        codigo = match_reg.group(1).upper()
                        descricao = match_reg.group(2).strip()
                        
                        ultimo_registro = codigo
                        registros[codigo] = {
                            "codigo": codigo,
                            "descricao": descricao,
                            "nivel": 1, # Default
                            "ocorrencia": "1:1", # Default
                            "campos": [] # Futuramente extrair os campos das tabelas
                        }
                        continue
                    
                    if ultimo_registro:
                        # Procurar Nível e Ocorrência no parágrafo seguinte ao título
                        match_niv = regex_nivel.search(linha)
                        if match_niv:
                            registros[ultimo_registro]["nivel"] = int(match_niv.group(1))
                            
                        match_oco = regex_ocorrencia.search(linha)
                        if match_oco:
                            registros[ultimo_registro]["ocorrencia"] = match_oco.group(1).strip()

    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return
        
    print(f"Foram encontrados {len(registros)} registros no manual.")
    
    # Salvar em JSON
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({"registros": registros}, f, ensure_ascii=False, indent=4)
        
    print(f"Base de Conhecimento salva em: {output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestor de Manuais do SPED em PDF")
    parser.add_argument("--pdf", required=True, help="Caminho para o PDF do Manual")
    parser.add_argument("--obrigacao", required=True, choices=['ecd', 'ecf'], help="Tipo da obrigação (ecd ou ecf)")
    
    args = parser.parse_args()
    
    output_path = os.path.join(os.path.dirname(__file__), '..', 'knowledge_base', f"{args.obrigacao}_rules.json")
    output_path = os.path.abspath(output_path)
    
    extract_sped_layout(args.pdf, output_path)
