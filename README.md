# Imports Sys

Sistema web mobile-first para controle financeiro de importacao e revenda de smartphones.

Estoque por serial, custo real auditavel, simulacao de preco e margem liquida em tempo real.

## Stack

- Python 3.12 / Flask
- SQLAlchemy + SQLite (WAL mode)
- Jinja2 + TailwindCSS + DataTables
- Gunicorn (producao, 1 worker)

## Funcionalidades

- **Dashboard** — KPIs: estoque, valor investido, lucro liquido, margem
- **Estoque** — tabela com edicao inline (holder, status), busca, criacao de unidades
- **Detalhe da Unidade** — custos (CRUD), simulador de preco, registro de venda
- **Lotes** — cadastro de compras, rateio proporcional de custos por lote
- **Vendas** — historico com receita, lucro e margem por unidade
- **Login** — autenticacao simples (1 usuario) via variaveis de ambiente

## Variaveis de ambiente

| Variavel | Obrigatoria | Descricao |
|----------|-------------|-----------|
| `SECRET_KEY` | Sim | Chave secreta para sessoes Flask |
| `ADMIN_USER` | Nao | Usuario de login (default: `admin`) |
| `ADMIN_PASSWORD` | Sim | Senha de login |
| `DATABASE_PATH` | Nao | Caminho do banco SQLite (default: `instance/app.db`) |

## Rodar local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export SECRET_KEY="sua-chave-secreta"
export ADMIN_PASSWORD="sua-senha"

python app.py
```

Acesse http://localhost:5000 e faca login com `admin` / sua senha.

## Docker

```bash
# Criar arquivo .env
cat > .env <<EOF
SECRET_KEY=troque-por-chave-segura
ADMIN_USER=admin
ADMIN_PASSWORD=troque-por-senha-segura
EOF

docker compose up -d --build
```

O banco SQLite fica persistido em `./data/app.db` no host.

### Backup e integridade

Os scripts estao em `scripts/`:

```bash
# Backup manual (dentro do container)
docker compose exec web bash scripts/backup_sqlite.sh

# Verificacao de integridade
docker compose exec web bash scripts/check_integrity.sh
```

#### Crontab no host (exemplo)

```cron
# Backup diario as 2h
0 2 * * * cd /srv/vendas-importados && docker compose exec -T web bash scripts/backup_sqlite.sh >> /var/log/vendas-backup.log 2>&1

# Integrity check diario as 3h
0 3 * * * cd /srv/vendas-importados && docker compose exec -T web bash scripts/check_integrity.sh >> /var/log/vendas-integrity.log 2>&1
```

### Restaurar backup

```bash
docker compose stop web
cp ./data/backups/app_YYYYMMDD_HHMMSS.db ./data/app.db
docker compose start web
```

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
| PATCH | `/api/sale/<id>` | Atualizar venda |
| GET | `/api/kpis` | Metricas do dashboard |

Todas as rotas da API requerem autenticacao (sessao). Respostas de erro retornam JSON `{"error": "..."}` com HTTP 4xx/5xx.

## Testes

```bash
pytest tests/ -v
```
