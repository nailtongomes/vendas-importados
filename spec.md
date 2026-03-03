# SPEC.MD — Sistema Pessoal de Importação e Vendas

## 1. Objetivo técnico

Construir um sistema web **mobile-first**, de uso individual, com:

* consulta de estoque em 1 toque
* precificação rápida durante negociação
* cálculo de margem líquida auditável
* edição direta em tabelas com AJAX

Sem complexidade de ERP, sem multiusuário.

---

## 2. Stack

### Backend

* Docker
* Python 3.x
* Flask
* SQLAlchemy
* Flask-Migrate (Alembic)
* SQLite

### Frontend

* Jinja2
* TailwindCSS
* DataTables (modo **client-side**)
* jQuery (somente para DataTables)
* AJAX via `fetch`

### Precisão numérica

* `Decimal` para valores financeiros
* Colunas `NUMERIC(12,2)` para BRL
* `NUMERIC(12,6)` para câmbio

---

## 3. Arquitetura

```
/app
  /models
  /services
  /routes
  /templates
  /static
```

Separação obrigatória:

* **models** → estrutura do banco
* **services** → regras de negócio e cálculos
* **routes** → HTML + APIs JSON

---

## 4. Conceitos de domínio

### Lote

Representa o fechamento da compra com:

* data
* fornecedor
* câmbio fixo

Após a conversão para BRL, o câmbio não é mais usado em cálculos futuros.

---

### Unidade

Cada aparelho físico com:

* serial único
* custo em USD
* lote de origem
* holder (texto livre)
* status

---

### Custos por unidade

Sempre em BRL.

Tipos:

* freight_intl
* freight_br
* insurance
* card_fee / iof
* import_tax
* broker_fee
* other
* invoice_tax

Origem:

* `manual`
* `allocated` (rateio de lote)

---

### Venda

Sempre vinculada a **uma unidade**.

Contém:

* preço de venda
* comissão fixa
* data
* canal (opcional)

---

## 5. Regras de negócio

### 5.1 Custo base da unidade

```
base_brl = usd_cost * exchange_rate_do_lote
```

---

### 5.2 Custo total da unidade

```
total_cost_brl = base_brl + SUM(unit_cost.brl_value)
```

---

### 5.3 Margem líquida

```
net_profit = sell_price_brl
             - total_cost_brl
             - commission_brl

net_margin = net_profit / sell_price_brl
```

---

### 5.4 Estoque

Status possíveis:

* AVAILABLE
* SOLD
* DEFECT
* RETURNED (preparado para futuro)

Movimentações:

* entrada (criação da unit)
* venda
* devolução
* perda/defeito

---

### 5.5 Rateio proporcional de custos do lote

Base de rateio:

```
proporção = usd_cost_da_unit / soma_usd_cost_do_lote
```

Processo:

1. remover todos os `unit_cost` com:

   * source = allocated
   * lot_id correspondente
2. recalcular valores proporcionais
3. recriar os `unit_cost`
4. gerar novo `allocation_run_id`

Nunca altera custos manuais.

---

### 5.6 Comissão

* valor fixo por unidade
* lançada junto com a venda

---

### 5.7 Estoque em R$

Valor do estoque:

```
SUM(total_cost_brl das units AVAILABLE)
```

---

## 6. Modelo de dados

### product_model

* id
* name
* storage_gb
* variant

---

### purchase_lot

* id
* purchased_at
* supplier
* exchange_rate
* notes

---

### unit

* id
* serial (unique)
* product_model_id
* purchase_lot_id
* usd_cost
* status
* holder
* created_at

---

### unit_cost

* id
* unit_id
* cost_type
* brl_value
* source (manual | allocated)
* lot_id (nullable)
* allocation_run_id (nullable)
* notes
* created_at

---

### sale

* id
* unit_id (unique)
* sold_at
* sell_price_brl
* commission_brl
* channel
* notes

---

## 7. APIs

### Units

#### GET /api/units

Retorna todas as unidades necessárias para a tela.

Campos calculados já incluídos:

* total_cost_brl
* status
* holder
* model_label

---

#### PATCH /api/unit/<id>

Permite editar:

* holder
* status
* usd_cost
* product_model_id

---

#### POST /api/unit/<id>/sell

Ação transacional:

1. cria sale
2. muda status para SOLD

---

### Custos

#### GET /api/unit/<id>/costs

#### POST /api/unit/<id>/costs

#### PATCH /api/cost/<id>

#### DELETE /api/cost/<id>

---

### Rateio de lote

#### POST /api/lot/<id>/allocate

Payload exemplo:

```json
{
  "freight_intl_total": 5000,
  "insurance_total": 800
}
```

---

### KPIs

#### GET /api/kpis?from=YYYY-MM-DD&to=YYYY-MM-DD

Retorna:

* vendas no período
* lucro líquido
* margem
* valor em estoque
* lucro por lote

---

## 8. UI

### 8.1 Estoque (acesso principal)

DataTable com:

* Serial
* Modelo
* Holder (editável)
* Custo total
* Status (editável)
* Ações:

  * Vender
  * Detalhes
  * WhatsApp

---

### 8.2 Detalhe da unidade

Blocos:

1. Dados da unidade
2. Tabela de custos (CRUD inline)
3. Simulador de preço
4. Botão “Registrar venda”

Simulador não persiste dados.

---

### 8.3 Dashboard

Cards:

* unidades em estoque
* valor do estoque
* vendas no período
* lucro líquido
* margem líquida
* lucro por lote

---

## 9. Edição inline (sem DataTables Editor)

Padrão:

1. clique na célula
2. vira input/select
3. on blur → PATCH via AJAX
4. sucesso → atualiza linha

---

## 10. Transações críticas

Devem usar commit/rollback:

* venda
* rateio de lote
* alteração de usd_cost

---

## 11. Performance

DataTables client-side:

* carregar somente dados necessários por tela
* evitar joins pesados na API
* retornar campos já calculados

---

## 12. Segurança (nível MVP)

Opções:

* uso local sem autenticação
  ou
* Basic Auth via nginx

---

## 13. Backup

Rotina:

* cópia diária do arquivo SQLite
* versionamento por data

---

## 14. Critérios de aceite técnico

* estoque abre em < 2s
* venda registrada em < 5s
* simulação de preço instantânea
* qualquer custo pode ser auditado até o lote de origem
* re-rateio não duplica custos

---

## 15. Fora do escopo

* multiusuário
* financeiro completo
* reservas
* integrações externas
* relatórios avançados
* cadastro formal de revendedores

Se fizer sentido, o próximo passo lógico é definir:

1. **estrutura real das respostas JSON de `/api/units` e `/api/kpis`** (isso dita toda a performance do front)
   ou
2. **mapa de serviços (`services.py`) com as funções puras de cálculo** para você já começar testável.

Qual dos dois você quer destravar primeiro?

