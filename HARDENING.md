# HARDENING.MD — O que evitar para não virar um app frágil + testes mínimos

## 1) Objetivo

Garantir que o sistema continue:

* **confiável financeiramente** (auditável)
* **estável** (não corrompe dados)
* **rápido** (uso diário no celular)
* **simples de manter** (por uma pessoa)

Este documento descreve:

* armadilhas comuns (o que evitar)
* contornos pragmáticos (como fazer sem complexidade)
* testes mínimos (para não quebrar sem perceber)

---

## 2) O que deve ser evitado (e como contornar)

### 2.1 “Regra de negócio no front-end”

**Problema:** se cálculos de custo/margem estiverem no JS, você terá divergência e bugs silenciosos.

**Contorno:**

* cálculo oficial sempre no backend (`services.py`)
* o front apenas exibe e envia inputs (preço, comissão, custos)

---

### 2.2 Atualizações parciais sem transação

**Problema:** vender unidade cria `sale` mas falha ao mudar `status` → estoque inconsistente.

**Contorno:**

* operações críticas em transação:

  * registrar venda
  * re-rateio
  * editar usd_cost e exchange_rate
* se falhar: rollback total

---

### 2.3 Re-rateio “misturando” custos manuais com alocados

**Problema:** re-rateio apaga custo manual sem querer, ou duplica custo alocado.

**Contorno:**

* `unit_cost.source = manual|allocated`
* `unit_cost.lot_id` + `allocation_run_id`
* re-rateio só deleta `allocated` daquele `lot_id`

---

### 2.4 Permitir editar valores sensíveis sem trilha

**Problema:** você muda `usd_cost` ou `exchange_rate` depois e não sabe por que o lucro “mudou”.

**Contorno (mínimo):**

* permitir edição, mas registrar evento:

  * `audit_log` simples (recomendado)
  * ou ao menos `notes` + `updated_at` nos campos sensíveis
* exibir “última alteração” no detalhe

---

### 2.5 Float para dinheiro

**Problema:** `float` gera erro de centavos, que vira erro de margem e quebra auditoria.

**Contorno:**

* `Decimal` no backend
* normalizar arredondamento:

  * BRL: 2 casas
  * câmbio: 4–6 casas
* no JSON, enviar como string/number já formatado (consistente)

---

### 2.6 Falta de constraints no banco

**Problema:** serial duplicado, venda duplicada, unidade sem lote, etc.

**Contorno:**

* constraints obrigatórias:

  * `unit.serial UNIQUE NOT NULL`
  * `sale.unit_id UNIQUE` (1 venda por unidade)
  * FKs com `ON DELETE RESTRICT` (evitar apagar histórico)
* `PRAGMA foreign_keys=ON`

---

### 2.7 “Delete em cascata” sem querer

**Problema:** apagar um lote apaga unidades e vendas e você perde auditoria.

**Contorno:**

* não permitir delete de entidades históricas (lote, unit vendida, sale)
* se precisar, usar status/arquivamento em vez de delete

---

### 2.8 N+1 queries e travamento no celular

**Problema:** DataTables client-side + backend devolvendo dados calculados por loop → lento.

**Contorno pragmático:**

* no endpoint do estoque, retornar só o necessário:

  * serial, modelo label, holder, status, total_cost_brl
* pré-calcular `total_cost_brl` em query agregada (join + sum) ou via view/CTE
* pagina HTML leve (sem libs extras)

---

### 2.9 Inputs sem validação (principalmente AJAX inline)

**Problema:** usuário digita “5,00” vs “5.00”, campo vazio, texto em número, etc.

**Contorno:**

* validação no backend (sempre)
* aceitar formatos brasileiros com parsing controlado (ou padronizar input numérico)
* retornar erro JSON com mensagem curta para toast

---

### 2.10 Sem backup e sem migração

**Problema:** um bug ou migração errada corrompe o SQLite e você perde tudo.

**Contorno mínimo:**

* backup diário do arquivo `.db` com timestamp
* migrations com Alembic
* antes de migrar: copiar DB e rodar migração em cópia

---

## 3) Testes mínimos (o “cinto de segurança”)

### 3.1 Testes de unidade (services.py)

Ferramenta: `pytest`

#### T01 — custo base

* dado: usd_cost e câmbio do lote
* espera: `base_brl = usd_cost * exchange_rate` (Decimal)

#### T02 — custo total

* dado: base_brl + lista de UnitCost
* espera: soma correta com 2 casas

#### T03 — margem líquida

* dado: sell_price_brl, commission_brl, total_cost_brl
* espera: lucro e margem corretos (inclui caso prejuízo)

#### T04 — rateio proporcional

* dado: 3 units com usd_cost diferentes + custo total lote
* espera:

  * soma dos rateios = total do lote (com política de arredondamento definida)
  * proporção respeitada
  * re-rateio substitui apenas `allocated`

> Observação crítica: definir regra de arredondamento para rateio para evitar “sobrar 0,01”.
> Ex.: distribuir o resto (centavos) para as maiores frações.

---

### 3.2 Testes de integração (API + DB em memória)

Ferramenta: Flask test client + SQLite in-memory (ou arquivo temp)

#### I01 — registrar venda é transacional

* cria unit AVAILABLE
* chama `POST /api/unit/<id>/sell`
* espera:

  * sale criada
  * unit.status = SOLD
  * se falhar em uma parte, nada persiste

#### I02 — serial único

* tenta criar duas units com mesmo serial
* espera: erro e nenhum registro duplicado

#### I03 — 1 venda por unidade

* vende unidade uma vez
* tenta vender de novo
* espera: erro de regra/constraint

#### I04 — re-rateio não apaga manual

* criar custos manuais
* rodar rateio
* rodar re-rateio
* espera:

  * custos manuais permanecem
  * custos allocated substituídos (sem duplicar)

---

### 3.3 Teste de “smoke” end-to-end (mínimo)

Ferramenta: pode ser manual guiado por checklist (aceitável) ou Playwright (futuro)

#### S01 — fluxo diário

* criar lote
* criar 2 units com serial
* rodar rateio
* abrir estoque (carrega rápido)
* simular preço (ver margem)
* registrar venda (status muda e aparece em vendas)

Checklist de aceitação:

* nenhum erro no console
* sem dados inconsistentes (unit vendida fora da lista AVAILABLE)

---

## 4) Guardrails (regras de implementação)

* Nenhuma rota de “ação” sem transação
* Nenhum cálculo financeiro oficial no JS
* Nenhum uso de float para BRL/câmbio
* Re-rateio sempre por `allocated` + `lot_id`
* Proibir deletes de histórico (usar status)
* Backups automáticos do SQLite

---

## 5) Observabilidade mínima (sem stack complexa)

* logging estruturado no Flask:

  * rota, tempo de resposta, payload resumido
* mensagens de erro padronizadas em JSON:

  * `{"error": {"code": "...", "message": "..."}}`
* página de “saúde” opcional:

  * `GET /health` → ok

---

## 6) Política de evolução segura

Para qualquer mudança que mexa em:

* rateio
* cálculos de custo
* formato de dinheiro
* constraints

fazer sempre:

1. criar teste que reproduz o caso
2. mudar código
3. rodar testes
4. migrar em DB de cópia
5. só então aplicar na DB real

---

## 7) Definição de pronto (Done)

Um release está “pronto” quando:

* T01–T04 passam
* I01–I04 passam
* Smoke S01 validado (manual ou automatizado)
* backup do DB confirmado
* tempo de carregamento do estoque continua aceitável no celular

