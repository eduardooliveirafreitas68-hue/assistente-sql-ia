# Esquema do banco `delivery.db` (SQLite)

Banco com dados FICTÍCIOS de uma plataforma de delivery de comida, cobrindo
pedidos feitos entre 2025-01-01 e 2025-12-31.

## Convenções importantes

- Datas e horas são TEXT no formato ISO `YYYY-MM-DD HH:MM:SS` (datas de cadastro: `YYYY-MM-DD`).
  Use as funções do SQLite: `date()`, `strftime('%Y-%m', coluna)`, `strftime('%H', coluna)`, `julianday()`.
- Diferença em minutos entre duas datas: `(julianday(fim) - julianday(inicio)) * 24 * 60`.
- Valores monetários estão em reais (R$), tipo REAL.
- Um pedido está **atrasado** quando `status = 'entregue' AND data_entrega > previsao_entrega`.
- Pedidos cancelados têm `data_entrega` NULL e podem ter `entregador_id` NULL.
- Taxa de atraso = pedidos atrasados / pedidos entregues (cancelados não entram na conta).
- Vendas (faturamento, itens vendidos, quantidade vendida, produtos mais vendidos) consideram apenas
  pedidos com `status = 'entregue'`: pedido cancelado não é venda.
- Horário de pico do jantar: pedidos com hora entre 18 e 21 (inclusive).

## Tabelas

### clientes
| coluna | tipo | descrição |
|---|---|---|
| id | INTEGER PK | identificador do cliente |
| nome | TEXT | nome do cliente |
| cidade | TEXT | cidade: 'São Paulo', 'Porto Alegre', 'Osasco', 'Curitiba', 'Belo Horizonte', 'Recife' |
| data_cadastro | TEXT | data de cadastro na plataforma (YYYY-MM-DD) |

### restaurantes
| coluna | tipo | descrição |
|---|---|---|
| id | INTEGER PK | identificador do restaurante |
| nome | TEXT | nome do restaurante |
| categoria | TEXT | 'Pizza', 'Japonesa', 'Hambúrguer', 'Brasileira', 'Saudável', 'Doces', 'Mexicana' |
| cidade | TEXT | cidade do restaurante (mesmos valores de clientes.cidade) |
| data_cadastro | TEXT | data de entrada na plataforma (YYYY-MM-DD) |

### entregadores
| coluna | tipo | descrição |
|---|---|---|
| id | INTEGER PK | identificador do entregador |
| nome | TEXT | nome do entregador |
| veiculo | TEXT | 'moto', 'bicicleta' ou 'carro' |
| cidade | TEXT | cidade onde atua |

### pedidos
| coluna | tipo | descrição |
|---|---|---|
| id | INTEGER PK | identificador do pedido |
| cliente_id | INTEGER FK → clientes.id | quem fez o pedido |
| restaurante_id | INTEGER FK → restaurantes.id | restaurante do pedido |
| entregador_id | INTEGER FK → entregadores.id | entregador (pode ser NULL em cancelados) |
| data_pedido | TEXT | data e hora em que o pedido foi feito |
| previsao_entrega | TEXT | data e hora prometida para a entrega |
| data_entrega | TEXT | data e hora real da entrega (NULL se cancelado) |
| status | TEXT | 'entregue' ou 'cancelado' |
| distancia_km | REAL | distância entre restaurante e cliente, em km |
| valor_itens | REAL | soma dos itens (R$) |
| taxa_entrega | REAL | taxa de entrega cobrada (R$); 0 quando valor_itens >= 100 |
| valor_total | REAL | valor_itens + taxa_entrega (R$) |
| forma_pagamento | TEXT | 'cartao_credito', 'pix', 'cartao_debito' ou 'dinheiro' |

### itens_pedido
| coluna | tipo | descrição |
|---|---|---|
| id | INTEGER PK | identificador do item |
| pedido_id | INTEGER FK → pedidos.id | pedido ao qual o item pertence |
| produto | TEXT | nome do produto (ex.: 'Pizza Calabresa', 'Açaí 500ml') |
| quantidade | INTEGER | quantidade comprada |
| preco_unitario | REAL | preço de uma unidade (R$) |

### avaliacoes
| coluna | tipo | descrição |
|---|---|---|
| pedido_id | INTEGER PK, FK → pedidos.id | pedido avaliado (no máximo uma avaliação por pedido) |
| nota | INTEGER | nota de 1 a 5 |
| data_avaliacao | TEXT | data e hora da avaliação |

## Relacionamentos

- clientes 1 — N pedidos
- restaurantes 1 — N pedidos
- entregadores 1 — N pedidos
- pedidos 1 — N itens_pedido
- pedidos 1 — 0..1 avaliacoes
