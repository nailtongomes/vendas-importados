# Imports Sys

Sistema web mobile-first para controle financeiro de importacao e revenda de smartphones.

Estoque por serial, custo real auditavel, simulacao de preco e margem liquida em tempo real.

## Stack

- Python 3.12 / Flask
- SQLAlchemy + SQLite
- Jinja2 + TailwindCSS + DataTables
- Gunicorn (producao)

## Funcionalidades

- **Dashboard** — KPIs: estoque, valor investido, lucro liquido, margem
- **Estoque** — tabela com edicao inline (holder, status), busca, criacao de unidades
- **Detalhe da Unidade** — custos (CRUD), simulador de preco, registro de venda
- **Lotes** — cadastro de compras, rateio proporcional de custos por lote
- **Vendas** — historico com receita, lucro e margem por unidade

## Rodar local

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
python app.py
```

Acesse http://localhost:5000

## Docker

```bash
docker compose up -d --build
```

O banco SQLite fica persistido no volume `imports-data`.

## API

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/units` | Listar unidades com custo total |
| POST | `/api/unit` | Criar unidade |
| PATCH | `/api/unit/<id>` | Atualizar holder/status/usd_cost |
| GET | `/api/unit/<id>/costs` | Listar custos da unidade |
| POST | `/api/unit/<id>/costs` | Adicionar custo manual |
| DELETE | `/api/cost/<id>` | Remover custo manual |
| POST | `/api/unit/<id>/sell` | Registrar venda |
| GET | `/api/unit/<id>/whatsapp` | Texto para WhatsApp |
| GET | `/api/lots` | Listar lotes |
| POST | `/api/lots` | Criar lote |
| GET | `/api/lot/<id>/units` | Unidades de um lote |
| POST | `/api/lot/<id>/allocate` | Ratear custos do lote |
| GET | `/api/sales` | Historico de vendas |
| GET | `/api/kpis` | Metricas do dashboard |

## Testes

```bash
pytest tests/ -v
```
