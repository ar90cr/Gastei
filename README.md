# Gastei

Aplicação web pessoal de finanças, mobile-first e compatível com PWA.

## V2 funcional

- Dashboard financeiro
- Receitas e despesas
- Transferências entre contas
- Cartões, compras e parcelamentos
- Investimentos
- Metas financeiras
- Saúde financeira
- Programas e regras de recompensas
- Automóveis e manutenção
- Exportação JSON
- PWA com manifest e service worker
- PostgreSQL no Render e SQLite como fallback local

## Deploy

O projeto usa Docker/Uvicorn. No Render, mantenha o PostgreSQL existente e a variável `DATABASE_URL` configurada.

Não é necessário recriar o banco para instalar esta versão.
