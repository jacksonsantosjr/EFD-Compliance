# -*- coding: utf-8 -*-
"""
Tabela de Regras Semânticas — CFOP × CST × NCM.
Cada regra define uma combinação inválida ou suspeita entre campos do SPED.
Este arquivo é puramente de dados; a lógica de aplicação fica no SemanticValidator.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# GRUPO 1: CFOP × CST — Regras Absolutas de Compatibilidade
# ═══════════════════════════════════════════════════════════════════════════════

REGRAS_CFOP_CST = [
    {
        "code": "SEM-001",
        "title": "Saída tributada integral sem destaque de ICMS",
        "severity": "critical",
        "cfop_starts": ["5", "6"],          # Saídas internas e interestaduais
        "cst_values": ["000", "00"],        # Tributada integralmente (origem 0 + CST 00)
        "check": "saida_tributada_sem_icms",
        "description": (
            "Operação de saída com CST 00 (Tributada Integralmente) exige que os campos "
            "VL_BC_ICMS e ALIQ_ICMS estejam preenchidos com valores maiores que zero. "
            "A ausência de destaque de ICMS em operação tributada integral configura "
            "inconsistência passível de autuação."
        ),
        "legal_ref": "RICMS-SP, Art. 182 c/c Convênio SINIEF s/n, Art. 5º",
    },
    {
        "code": "SEM-002",
        "title": "Crédito de ICMS em operação Isenta/Não Tributada",
        "severity": "critical",
        "cfop_starts": ["1", "2"],           # Entradas
        "cst_values": ["040", "040", "041", "40", "41"],
        "check": "entrada_isenta_com_credito",
        "description": (
            "Operação de entrada com CST 40 (Isenta) ou 41 (Não Tributada) não gera "
            "direito a crédito de ICMS. Se houver VL_ICMS destacado nesta combinação, "
            "o crédito é indevido e sujeito a glosa."
        ),
        "legal_ref": "RICMS-SP, Art. 66, V; CF/88, Art. 155, §2º, II, 'a'",
    },
    {
        "code": "SEM-003",
        "title": "Revenda simples com CST de Substituição Tributária",
        "severity": "warning",
        "cfop_exact": ["5102", "6102", "5403", "6403"],
        "cst_endswith": ["10", "30", "70"],  # CSTs de ST na operação própria
        "check": "revenda_com_st_indevida",
        "description": (
            "Os CFOPs 5.102/6.102 (Venda de mercadoria adquirida de terceiros) indicam "
            "revenda simples, porém o CST utilizado (10/30/70) sugere incidência de ST "
            "na operação própria. Verifique se a mercadoria realmente está sujeita à ST "
            "ou se o CST correto seria 060 (ICMS cobrado anteriormente por ST)."
        ),
        "legal_ref": "RICMS-SP, Art. 313-A e seguintes; Convênio SINIEF s/n, Art. 5º",
    },
    {
        "code": "SEM-004",
        "title": "Venda com ST sem CST de Substituição Tributária",
        "severity": "critical",
        "cfop_exact": ["5401", "6401", "5403", "6403", "5405", "6405"],
        "cst_not_endswith": ["10", "30", "60", "70"],
        "check": "venda_st_sem_cst_st",
        "description": (
            "O CFOP indica operação com mercadoria sujeita à Substituição Tributária, "
            "porém o CST utilizado não corresponde a nenhum dos CSTs de ST "
            "(10, 30, 60 ou 70). Essa inconsistência pode gerar autuação por "
            "destaque indevido ou falta de recolhimento da ST."
        ),
        "legal_ref": "RICMS-SP, Art. 313-A; Convênio ICMS 142/2018",
    },
    {
        "code": "SEM-005",
        "title": "Bonificação/Doação com destaque de ICMS",
        "severity": "warning",
        "cfop_exact": ["5910", "6910", "5911", "6911"],
        "cst_values": ["000", "00"],
        "check": "bonificacao_com_icms",
        "description": (
            "Operações de bonificação, doação ou brinde (CFOPs 5.910/6.910) geralmente "
            "são isentas ou não tributadas em diversos estados. Verificar se há convênio "
            "ou protocolo que autorize a tributação integral nesta operação."
        ),
        "legal_ref": "RICMS-SP, Anexo I, Art. 3º; Convênio ICMS 29/81",
    },
    {
        "code": "SEM-006",
        "title": "CFOP genérico (x.949) com tributação integral",
        "severity": "warning",
        "cfop_endswith": ["949"],
        "cst_values": ["000", "00"],
        "check": "cfop_generico_tributado",
        "description": (
            "O CFOP x.949 (Outras saídas/entradas não especificadas) é genérico e seu uso "
            "com CST 00 (tributada integral) merece atenção especial. "
            "Verifique se não existe CFOP mais específico para a operação."
        ),
        "legal_ref": "Convênio SINIEF s/n, Anexo de CFOPs",
    },
    {
        "code": "SEM-007",
        "title": "Origem de importação com NCM nacional",
        "severity": "warning",
        "cst_startswith": ["1", "2", "3", "8"],  # Origens de importação
        "check": "origem_importacao_verificar",
        "description": (
            "O CST indica origem estrangeira (1, 2, 3 ou 8), porém o item deve ter "
            "NCM compatível e estar cadastrado corretamente no registro 0200. "
            "Verifique se a classificação fiscal e a origem estão corretas."
        ),
        "legal_ref": "Ajuste SINIEF 20/2012; Resolução CAMEX nº 125/2016",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# GRUPO 2: CFOP × NCM — Compatibilidade de Natureza da Operação
# ═══════════════════════════════════════════════════════════════════════════════

REGRAS_CFOP_NCM = [
    {
        "code": "SEM-010",
        "title": "Transferência para industrialização com NCM de serviço",
        "severity": "warning",
        "cfop_exact": ["5151", "6151", "5152", "6152"],
        "ncm_starts": ["00"],
        "check": "transferencia_ncm_servico",
        "description": (
            "O CFOP indica transferência para industrialização/produção, mas o NCM "
            "do item começa com '00', que é reservado para serviços. "
            "Verifique se o NCM está cadastrado corretamente no registro 0200."
        ),
        "legal_ref": "Guia Prático EFD, Registro 0200, campo COD_NCM",
    },
    {
        "code": "SEM-011",
        "title": "Venda de produção industrial com NCM genérico",
        "severity": "warning",
        "cfop_exact": ["5101", "6101", "5111", "6111", "5116", "6116"],
        "ncm_exact": ["99999999", "00000000"],
        "check": "producao_ncm_generico",
        "description": (
            "O CFOP indica venda de produção própria ou industrialização por encomenda, "
            "mas o NCM é genérico (99999999 ou 00000000). Operações industriais devem ter "
            "NCM específico e válido."
        ),
        "legal_ref": "Guia Prático EFD, Registro 0200; TEC/TIPI",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# GRUPO 3: CST × Valores — Consistência Financeira nos Itens (C170)
# ═══════════════════════════════════════════════════════════════════════════════

REGRAS_CST_VALORES = [
    {
        "code": "SEM-020",
        "title": "CST 00 (Tributada integral) sem Base de Cálculo ou Alíquota",
        "severity": "critical",
        "cst_endswith": ["00"],
        "check": "cst00_sem_bc",
        "description": (
            "Item com CST terminado em 00 (Tributada Integralmente) deve possuir "
            "VL_BC_ICMS > 0 e ALIQ_ICMS > 0. A ausência desses valores indica "
            "erro na escrituração e pode gerar diferença de imposto."
        ),
        "legal_ref": "RICMS-SP, Art. 37; Convênio SINIEF s/n, Art. 5º",
    },
    {
        "code": "SEM-021",
        "title": "CST 20 (Redução de BC) sem valor de redução",
        "severity": "warning",
        "cst_endswith": ["20"],
        "check": "cst20_sem_reducao",
        "description": (
            "Item com CST terminado em 20 (Com Redução de Base de Cálculo) deve possuir "
            "VL_RED_BC > 0 no registro C190 consolidado. A redução declarada mas não "
            "aplicada indica inconsistência."
        ),
        "legal_ref": "RICMS-SP, Anexo II; Convênio ICMS 52/91",
    },
    {
        "code": "SEM-022",
        "title": "ICMS destacado em operação Isenta/NT/Suspensão",
        "severity": "critical",
        "cst_endswith": ["40", "41", "50"],
        "check": "isenta_com_icms",
        "description": (
            "Item com CST 40 (Isenta), 41 (Não Tributada) ou 50 (Suspensão) não deve "
            "possuir VL_ICMS > 0. O destaque de ICMS em operação isenta/NT/suspensa "
            "configura crédito indevido se apropriado pelo destinatário."
        ),
        "legal_ref": "RICMS-SP, Art. 7º e Art. 8º; CF/88, Art. 155, §2º, II",
    },
    {
        "code": "SEM-023",
        "title": "Diferimento total com alíquota cheia",
        "severity": "warning",
        "cst_endswith": ["51"],
        "check": "diferimento_aliq_cheia",
        "description": (
            "Item com CST 51 (Diferimento) em combinação com alíquota integral (18%) "
            "e VL_ICMS > 0 é suspeito. Em operações com diferimento total, "
            "o ICMS próprio deve ser zero ou parcial (diferimento parcial)."
        ),
        "legal_ref": "RICMS-SP, Art. 428 e seguintes",
    },
    {
        "code": "SEM-024",
        "title": "CST 60 (ICMS cobrado por ST) com destaque de ICMS próprio",
        "severity": "critical",
        "cst_endswith": ["60"],
        "check": "cst60_com_icms_proprio",
        "description": (
            "Item com CST 60 indica que o ICMS já foi recolhido anteriormente por "
            "Substituição Tributária. Não deve haver VL_ICMS (próprio) > 0 nesta "
            "operação. Se houver, o imposto estará sendo cobrado em duplicidade."
        ),
        "legal_ref": "RICMS-SP, Art. 274; Convênio ICMS 142/2018",
    },
]
