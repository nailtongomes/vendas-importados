# PRD — Sistema Pessoal de Importação e Vendas

## 1. Visão Geral

Sistema web mobile-first, de uso individual, para controle **financeiro auditável** da operação de importação e revenda de smartphones.

O foco é **velocidade de decisão** no dia a dia e **rastreabilidade completa de custos e margens**, sem complexidade operacional.

Não é um ERP.
É uma ferramenta de apoio à precificação, controle de estoque por unidade (serial) e análise de lucro.

---

## 2. Objetivo do Produto

Permitir que, em até **30 segundos no celular**, seja possível:

* visualizar o estoque disponível
* saber quanto já foi vendido em um período
* enxergar a margem líquida real

com base em dados confiáveis e auditáveis.

---

## 3. Job To Be Done

### Job principal

> “Quando eu estiver negociando um aparelho ou avaliando meu negócio no dia a dia, quero ver rapidamente meu estoque, entender meu custo real e minha margem, para decidir o preço e vender com segurança sem depender de planilhas.”

### Jobs funcionais

* Registrar uma nova compra (lote + unidades com serial)
* Calcular custo total por unidade automaticamente
* Simular preço de venda com margem líquida
* Registrar venda vinculada ao serial
* Ver lucro por lote
* Ver capital imobilizado em estoque

### Jobs emocionais

* Ter segurança de que não estou vendendo com prejuízo
* Parar de depender de planilhas dispersas
* Tomar decisão rápida enquanto falo com cliente

### Jobs sociais

* Passar preço rapidamente para revendedores/clientes
* Compartilhar texto de venda com aparência profissional

---

## 4. Princípios do Produto

* Mobile first
* 1 toque para estoque
* Fluxo mínimo (sem cadastros desnecessários)
* Financeiramente auditável
* Operável por uma única pessoa

---

## 5. Escopo do MVP

### 5.1 Entrada de compra (lote)

Registrar:

* data da compra
* fornecedor
* câmbio do dia (fixo e histórico)
* aparelhos do lote:

  * modelo
  * armazenamento
  * serial/IMEI
  * custo em USD

### 5.2 Custos por unidade

Custos sempre em **BRL** e auditáveis:

* frete internacional (rateado proporcional ao valor do aparelho)
* frete interno
* seguro
* IOF / taxa de cartão
* taxa de importação
* taxa do intermediário
* outros custos

Imposto: apenas valor final quando existir nota.

---

### 5.3 Formação de custo

Custo total da unidade:

```
(custo USD × câmbio do lote)
+ soma dos custos unitários em BRL
```

Após isso, o câmbio não é mais utilizado.

---

### 5.4 Precificação

Permitir:

* informar preço de venda manual
* visualizar:

  * lucro bruto
  * comissão
  * margem líquida

A margem não é fixa — é orientada pelo mercado.

---

### 5.5 Venda

Registrar:

* serial vendido
* valor da venda
* comissão (valor fixo)
* data
* canal (opcional)
* observações

Estoque é atualizado automaticamente.

---

### 5.6 Controle de estoque

Visualizar por:

* modelo
* armazenamento
* com quem está:

  * comigo
  * revendedor

Status:

* disponível
* vendido
* defeito/perda (futuro)

---

### 5.7 Dashboard (visão em 30 segundos)

Exibir:

* quantidade em estoque
* valor total em estoque (custo)
* vendas no período
* margem líquida no período
* lucro por lote

---

### 5.8 Compartilhamento

Gerar texto pronto para WhatsApp com:

* modelo
* armazenamento
* condição
* preço

---

## 6. Fora do Escopo do MVP

* controle financeiro completo (contas a pagar/receber)
* multiusuário
* reservas
* integração com marketplaces
* emissão de nota
* relatórios complexos
* controle de pagamento de comissões

---

## 7. Entidades Principais

### ProductModel

Representa a linha do aparelho
Ex: iPhone 15 Pro 256GB

### PurchaseLot

Agrupa:

* data
* fornecedor
* câmbio

### Unit

Representa o aparelho individual:

* serial
* modelo
* lote
* custo USD
* status
* localização (com quem está)

### UnitCost

Custos unitários em BRL com tipo e observação.

### Sale

Venda vinculada ao serial com valor, comissão e data.

---

## 8. Métricas de Sucesso

* Tempo para consultar estoque < 5 segundos
* Tempo para simular preço < 10 segundos
* Eliminação da necessidade de planilha no dia a dia
* Capacidade de auditar o custo de qualquer unidade vendida

---

## 9. Frequência de Uso

Uso diário:

* consultar estoque
* simular preço
* registrar venda

Uso semanal:

* analisar lucro por lote
* avaliar capital em estoque
* entender giro por modelo

---

## 10. Riscos

* Complexidade excessiva para uso individual
* Perda de velocidade por excesso de campos
* Não registrar custos no momento correto (quebra da auditoria)

---

## 11. Critérios de Sucesso do MVP

O sistema será considerado válido quando:

* substituir a planilha atual no fluxo diário
* permitir precificar durante uma negociação em tempo real
* mostrar lucro real sem cálculos manuais

---

## 12. Evoluções Futuras (não MVP)

* cadastro de revendedores
* histórico de garantia por serial
* leitura de serial por câmera
* sugestão automática de preço baseada em margem alvo
* relatórios de giro
* modo offline-first com sincronização

---

## 13. Stack Técnica (diretriz)

* Backend: Flask
* Banco: SQLite
* Frontend: HTML server-side simples
* UI: otimizada para celular
* Deploy: local ou VPS simples

---

## 14. Filosofia do Produto

Este sistema não existe para “controlar dados”.

Ele existe para:

* acelerar decisões
* proteger margem
* dar clareza sobre o capital

É uma ferramenta de operação diária, não um sistema administrativo.

