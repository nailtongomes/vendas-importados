# SCREENS.MD — Descrição das Telas (Mobile-first)

## 1. Princípios de UI

* Uso com **uma mão no celular**
* Acesso ao **estoque em 1 toque**
* Máximo de **2 níveis de navegação**
* Ações críticas sempre visíveis (sem menu escondido)
* Edição rápida sem reload de página
* Feedback visual imediato após salvar

---

## 2. Mapa de navegação

```text
Dashboard
   ↓
Estoque (principal)
   ↓
Detalhe da unidade
```

Ações globais acessíveis:

* ➕ Nova compra (lote)
* ➕ Nova unidade
* 📊 Vendas (lista)

---

## 3. Dashboard

### Objetivo

Responder em até **30 segundos**:

* quanto tenho em estoque
* quanto vendi
* quanto lucrei

### Layout

#### Cards principais

1. **Estoque (unidades)**
2. **Estoque (R$ custo)**
3. **Vendas no período**
4. **Lucro líquido**
5. **Margem líquida**

#### Seção: Lucro por lote

Lista curta:

* Lote
* Investimento
* Receita
* Lucro

#### Seção: Giro por modelo

* Modelo
* Qtde vendida
* Lucro total

### Interações

* Filtro por período (7d / 30d / personalizado)
* Clique em lote → abre lista de unidades do lote

---

## 4. Estoque (Tela principal do sistema)

### Objetivo

Ser a tela mais acessada do sistema.

Responder imediatamente:

* o que tenho disponível
* onde está cada aparelho
* quanto custou

---

### Estrutura

#### Barra superior

* Campo de busca (serial / modelo)
* Filtro rápido:

  * AVAILABLE
  * SOLD
  * DEFECT

#### DataTable

Colunas:

1. Serial
2. Modelo
3. Holder
4. Custo total (R$)
5. Status
6. Ações

---

### Edição inline

#### Holder

* toque → input texto
* blur → salva via AJAX

#### Status

* select:

  * AVAILABLE
  * SOLD
  * DEFECT

---

### Ações por linha

Botões:

* 💰 **Vender**
* 🔍 **Detalhes**
* 📲 **WhatsApp**

---

### Ação flutuante (FAB)

➕ Nova unidade

---

## 5. Detalhe da Unidade

### Objetivo

Ser a tela de:

* auditoria de custo
* simulação de preço
* registro da venda

---

### 5.1 Bloco: Dados principais

Exibir:

* Serial
* Modelo
* Lote
* Fornecedor
* Câmbio do lote
* USD cost
* Base em R$

Ações rápidas:

* Editar modelo
* Editar USD cost

---

### 5.2 Bloco: Custos

Tabela:

| Tipo | Valor (R$) | Origem | Ações |

Ações:

* ➕ Adicionar custo
* Editar inline
* Remover

Indicadores:

* Custo total atualizado em tempo real

---

### 5.3 Bloco: Simulador de preço

Campos:

* Preço de venda
* Comissão

Resultado instantâneo:

* Lucro líquido (R$)
* Margem (%)

Cores:

* vermelho → prejuízo
* verde → lucro

Não persiste dados.

---

### 5.4 Bloco: Registrar venda

Campos:

* Preço final
* Comissão
* Data
* Canal
* Observações

Botão:

**Confirmar venda**

Ação:

* cria sale
* muda status para SOLD
* redireciona para estoque

---

## 6. Tela de Lotes

### Objetivo

Controlar entradas e rateios.

---

### Lista de lotes

Colunas:

* Data
* Fornecedor
* Câmbio
* Qtde de unidades
* Investimento total
* Ações

Ações:

* Ver unidades
* Ratear custos

---

### Detalhe do lote

#### Informações

* data
* fornecedor
* câmbio

#### Unidades do lote

Lista simples.

---

#### Bloco: Rateio de custos

Inputs:

* frete internacional total
* seguro total
* taxa importação
* outros

Botão:

**Re-ratear custos**

Comportamento:

* mostra preview do valor por unidade
* confirmar → substitui custos rateados anteriores

---

## 7. Tela de Vendas

### Objetivo

Visão histórica rápida.

---

### Tabela

Colunas:

* Data
* Serial
* Modelo
* Preço venda
* Custo total
* Lucro líquido
* Comissão
* Canal

Filtros:

* Período
* Modelo

Resumo no topo:

* Receita total
* Lucro total
* Margem média

---

## 8. Modal: Nova unidade

Campos:

* Lote
* Modelo
* Serial
* USD cost
* Holder inicial

Botão:

**Salvar**

Após salvar:

* opção “adicionar outra”
* voltar para estoque

---

## 9. Modal: Novo custo

Campos:

* Tipo
* Valor
* Observação

Salvar → atualiza custo total instantaneamente.

---

## 10. WhatsApp (geração de texto)

Conteúdo:

```text
📱 {modelo}
💾 {armazenamento}
💰 R$ {preço}

Produto disponível.
```

Botões:

* Copiar texto
* Abrir WhatsApp

---

## 11. Estados de carregamento

* Skeleton nos cards do dashboard
* “Salvando…” na célula editada
* Toast de sucesso/erro

---

## 12. Responsividade

### Mobile

* tabela com scroll horizontal
* ações como ícones
* FAB visível

### Desktop

* tabela completa
* atalhos de teclado (futuro)

---

## 13. Fluxos críticos

### Venda em 3 toques

Estoque → Vender → Confirmar

---

### Simular preço durante negociação

Estoque → Detalhe → digitar preço → ver margem

---

### Entrada de nova compra

Lotes → Novo lote → adicionar unidades

---

## 14. Critérios de sucesso da UX

* consultar estoque em < 2 segundos
* simular preço sem navegar de tela
* registrar venda em < 5 segundos
* custo total sempre visível

---

## 15. Fora do escopo visual (MVP)

* gráficos complexos
* modo escuro
* personalização de layout
* múltiplos dashboards

