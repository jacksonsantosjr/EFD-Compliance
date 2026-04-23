# EFD Compliance — Status do Roadmap de Evolução
> Última atualização: 22/04/2026 — 17:35

---

## Visão Geral do Projeto

O **EFD Compliance** evoluiu de um validador estrutural básico para um **auditor fiscal de alto nível**, focado na "Malha Fina" da SEFAZ-SP. O diferencial competitivo é a **validação semântica** e o cruzamento inteligente de dados que o PVA (Programa Validador e Assinador) não realiza.

---

## Pipeline de Validação Atual (8 etapas)

```
1. MathValidator        → Fórmulas E110, G110, E520, Bloco 9
2. CrossBlockValidator  → C190×E110, E111×E110, G125×G110, H010×0200
3. SemanticValidator    → 14 regras CFOP×CST×NCM             ✅ NOVO
4. CadastralValidator   → Idoneidade CNPJ via 6 APIs         ✅ NOVO
5. UF Rules (SP)        → Tabela 5.1.1, CIAP, Bloco K, DIFAL
6. Score (6 faixas)     → Excelente → Inadequado
7. Relatório PDF/DOCX   → Dossiê Executivo completo
8. Dashboard React      → Visualização interativa
```

---

## Roadmap Detalhado

### ✅ FASE 1.A — Validador de Idoneidade Cadastral (CNPJ)
**Status: CONCLUÍDO** | Commit: `2c2c3c4`

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Serviço Round-Robin (6 APIs) | `validators/services/cnpj_service.py` | ✅ Criado |
| Motor de Validação Cadastral | `validators/cadastral_validator.py` | ✅ Criado |
| Pipeline assíncrona | `validators/base_validator.py` | ✅ Modificado |
| Rotas com await | `api/routes/upload.py` | ✅ Modificado |
| Testes adaptados | `tests/test_validators.py` | ✅ Modificado |

**O que faz:**
- Varre todos os CNPJs do registro 0150 (Participantes/Fornecedores)
- Consulta a situação cadastral na Receita Federal via 6 APIs gratuitas com balanceamento inteligente
- Se detectar CNPJ INAPTO/BAIXADO/SUSPENSO/NULO, rastreia as NFs de entrada no C100
- Calcula o valor exato do "Crédito de ICMS em Risco" e gera alerta CRITICAL

---

### ✅ FASE 1.B — Validador Semântico (CFOP × CST × NCM)
**Status: CONCLUÍDO** | Commit: `36fe354`

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Tabela de 14 regras fiscais | `knowledge_base/semantic_rules.py` | ✅ Criado |
| Motor de validação semântica | `validators/semantic_validator.py` | ✅ Criado |
| Integração na pipeline | `validators/base_validator.py` | ✅ Modificado |

**O que faz:**
- **Grupo 1 (7 regras):** Cruza CFOP × CST para detectar combinações ilegais (ex: crédito em operação isenta, revenda com ST indevida)
- **Grupo 2 (2 regras):** Cruza CFOP × NCM para verificar compatibilidade (ex: NCM de serviço em operação industrial)
- **Grupo 3 (5 regras):** Valida CST × Valores nos itens C170 (ex: CST 00 sem base de cálculo, CST 60 com ICMS próprio)
- Consolida alertas por combinação para não gerar ruído

---

### ✅ FASE 2 — Módulo Integrador XML × EFD
**Status: CONCLUÍDO** | Commit: `4a1b2c3`

**Objetivo:** Cruzar os XMLs das NF-es (arquivos .xml) com os registros escriturados no SPED, linha a linha, para detectar:
- NFs presentes no XML mas ausentes no SPED (omissão de receita)
- NFs no SPED com valores diferentes do XML (divergência de valores)
- Chaves de NF-e inválidas ou não encontradas

**Complexidade:** Alta — exige parser de XML (NF-e), upload de lotes de XMLs e cruzamento por chave de acesso.

---

### 🔲 FASE 3 — Auditor de Bloco K/H (Equação de Estoque)
**Status: PENDENTE**

**Objetivo:** Validar a consistência entre o Bloco K (Produção/Estoque) e o Bloco H (Inventário), aplicando a equação:
```
Estoque Inicial + Entradas - Saídas - Consumo = Estoque Final
```

**Complexidade:** Alta — exige leitura de múltiplos períodos e cruzamento de fichas de estoque.

---

## Métricas de Qualidade

| Métrica | Valor |
|---------|-------|
| Testes unitários | 88 (100% passando) |
| Regras de validação ativas | 14 semânticas + 8 cruzamento + 6 matemáticas + regras SP |
| APIs de CNPJ integradas | 6 (Round-Robin com cooldown) |
| Faixas de Score | 6 (Excelente → Inadequado) |
| Formatos de relatório | PDF + DOCX |

---

## Decisões Arquiteturais Tomadas

1. **Sem cache de CNPJ:** Consultas sempre em tempo real para garantir dados atualizados
2. **Profundidade máxima nos alertas:** Findings de idoneidade incluem valor do crédito em risco e NFs envolvidas
3. **Regras separadas da lógica:** `semantic_rules.py` contém apenas dados; novas regras podem ser adicionadas sem tocar no motor
4. **Consolidação inteligente:** Alertas semânticos são agrupados por CST×CFOP para não poluir o relatório
5. **Pipeline assíncrona:** O `base_validator` opera com `async/await` para suportar consultas de rede sem travar o servidor

---

## Próximos Passos (quando retomar)

1. **Testar em produção** — Subir um arquivo SPED real e verificar os novos findings no relatório PDF
2. **Avaliar prioridade** — Fase 2 (XML×EFD) ou Fase 3 (Bloco K/H)?
3. **Expansão de regras semânticas** — Adicionar regras específicas para operações de devolução, remessa para conserto, etc.
