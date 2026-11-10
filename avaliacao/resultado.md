# Resultado da avaliação

- Data: 2026-11-10 17:28
- Modelo: `claude-opus-5-5`
- **Acurácia: 18/18 (100.0%)**

| # | Pergunta | Resultado | Motivo |
|---|---|---|---|
| 1 | Quantos pedidos foram feitos em 2025? | ✅ | resultado igual ao gabarito |
| 2 | Quantos pedidos atrasaram em março de 2025? | ✅ | resultado igual ao gabarito |
| 3 | Qual a taxa de atraso (em %) por tipo de veículo do entregador? | ✅ | resultado igual ao gabarito |
| 4 | Qual o faturamento total (valor_total) por cidade dos clientes, considerando só pedidos entregues? | ✅ | resultado igual ao gabarito |
| 5 | Quais são as 5 categorias de restaurante com maior ticket médio (valor_total médio) em pedidos entregues? | ✅ | resultado igual ao gabarito |
| 6 | Qual a nota média das avaliações de pedidos atrasados e de pedidos entregues no prazo? | ✅ | números iguais ao gabarito (rótulos de texto diferentes) |
| 7 | Quantos pedidos foram cancelados em cada mês de 2025? | ✅ | resultado igual ao gabarito |
| 8 | Qual o tempo médio de entrega em minutos, considerando os pedidos entregues? | ✅ | resultado igual ao gabarito |
| 9 | Qual a taxa de atraso no horário de pico do jantar (18h às 21h) comparada com os outros horários? | ✅ | números iguais ao gabarito (rótulos de texto diferentes) |
| 10 | Quais os 2 produtos mais vendidos em quantidade? | ✅ | resultado igual ao gabarito |
| 11 | Qual a participação (%) de cada forma de pagamento no total de pedidos? | ✅ | resultado igual ao gabarito |
| 12 | Quantos pedidos tiveram frete grátis? | ✅ | resultado igual ao gabarito |
| 13 | Qual o restaurante com mais pedidos entregues em Porto Alegre? Mostre o nome e a quantidade. | ✅ | resultado igual ao gabarito |
| 14 | Quantos clientes diferentes fizeram pelo menos um pedido em dezembro de 2025? | ✅ | resultado igual ao gabarito |
| 15 | Qual a distância média, em km, dos pedidos atrasados entregues de bicicleta? | ✅ | resultado igual ao gabarito |
| 16 | Qual a porcentagem de pedidos entregues que receberam avaliação? | ✅ | resultado igual ao gabarito |
| 17 | Qual entregador fez mais entregas em São Paulo? Mostre nome, veículo e quantidade. | ✅ | resultado igual ao gabarito |
| 18 | Qual foi o salário médio dos entregadores em 2025? | ✅ | recusou corretamente |

## Detalhes

### #1 ✅ Quantos pedidos foram feitos em 2025?

**Explicação da IA:** Conta todos os pedidos feitos em 2025, tanto os entregues quanto os cancelados. A pergunta é sobre pedidos feitos e não sobre vendas, por isso os cancelados também entram.

**SQL da IA:**
```sql
SELECT COUNT(*) AS total_pedidos FROM pedidos WHERE strftime('%Y', data_pedido) = '2025'
```
**Resultado da IA:**
```
(12000,)
```
**SQL de referência:**
```sql
SELECT COUNT(*) AS total_pedidos FROM pedidos WHERE strftime('%Y', data_pedido) = '2025'
```
**Gabarito:**
```
(12000,)
```

### #2 ✅ Quantos pedidos atrasaram em março de 2025?

**Explicação da IA:** Conta os pedidos entregues após a previsão de entrega, ou seja, os pedidos atrasados. Considerei o mês pela data em que o pedido foi feito (março de 2025).

**SQL da IA:**
```sql
SELECT COUNT(*) AS pedidos_atrasados FROM pedidos WHERE status = 'entregue' AND data_entrega > previsao_entrega AND strftime('%Y-%m', data_pedido) = '2025-03'
```
**Resultado da IA:**
```
(179,)
```
**SQL de referência:**
```sql
SELECT COUNT(*) AS pedidos_atrasados FROM pedidos WHERE status = 'entregue' AND data_entrega > previsao_entrega AND strftime('%Y-%m', data_pedido) = '2025-03'
```
**Gabarito:**
```
(179,)
```

### #3 ✅ Qual a taxa de atraso (em %) por tipo de veículo do entregador?

**Explicação da IA:** Calcula, para cada tipo de veículo, a porcentagem de pedidos entregues que chegaram depois da previsão. Pedidos cancelados não entram na conta, seguindo a definição de taxa de atraso.

**SQL da IA:**
```sql
SELECT e.veiculo, COUNT(*) AS pedidos_entregues, SUM(CASE WHEN p.data_entrega > p.previsao_entrega THEN 1 ELSE 0 END) AS pedidos_atrasados, ROUND(100.0 * SUM(CASE WHEN p.data_entrega > p.previsao_entrega THEN 1 ELSE 0 END) / COUNT(*), 2) AS taxa_atraso_pct FROM pedidos p JOIN entregadores e ON e.id = p.entregador_id WHERE p.status = 'entregue' GROUP BY e.veiculo ORDER BY taxa_atraso_pct DESC
```
**Resultado da IA:**
```
('bicicleta', 3739, 1548, 41.4)
('carro', 1611, 235, 14.59)
('moto', 5949, 490, 8.24)
```
**SQL de referência:**
```sql
SELECT e.veiculo, ROUND(100.0 * SUM(CASE WHEN p.data_entrega > p.previsao_entrega THEN 1 ELSE 0 END) / COUNT(*), 2) AS taxa_atraso_pct FROM pedidos p JOIN entregadores e ON e.id = p.entregador_id WHERE p.status = 'entregue' GROUP BY e.veiculo
```
**Gabarito:**
```
('bicicleta', 41.4)
('carro', 14.59)
('moto', 8.24)
```

### #4 ✅ Qual o faturamento total (valor_total) por cidade dos clientes, considerando só pedidos entregues?

**Explicação da IA:** Soma o valor_total dos pedidos entregues, agrupando pela cidade do cliente. O resultado vem ordenado do maior para o menor faturamento.

**SQL da IA:**
```sql
SELECT c.cidade, ROUND(SUM(p.valor_total), 2) AS faturamento_total FROM pedidos p JOIN clientes c ON c.id = p.cliente_id WHERE p.status = 'entregue' GROUP BY c.cidade ORDER BY faturamento_total DESC
```
**Resultado da IA:**
```
('São Paulo', 363027.18)
('Porto Alegre', 233987.28)
('Curitiba', 164467.18)
('Belo Horizonte', 129659.0)
('Osasco', 103469.64)
... (6 linhas no total)
```
**SQL de referência:**
```sql
SELECT c.cidade, ROUND(SUM(p.valor_total), 2) AS faturamento FROM pedidos p JOIN clientes c ON c.id = p.cliente_id WHERE p.status = 'entregue' GROUP BY c.cidade
```
**Gabarito:**
```
('Belo Horizonte', 129659.0)
('Curitiba', 164467.18)
('Osasco', 103469.64)
('Porto Alegre', 233987.28)
('Recife', 74714.47)
... (6 linhas no total)
```

### #5 ✅ Quais são as 5 categorias de restaurante com maior ticket médio (valor_total médio) em pedidos entregues?

**Explicação da IA:** Calcula a média do valor_total dos pedidos entregues em cada categoria de restaurante e mostra as 5 maiores. Pedidos cancelados foram desconsiderados.

**SQL da IA:**
```sql
SELECT r.categoria, ROUND(AVG(p.valor_total), 2) AS ticket_medio, COUNT(*) AS total_pedidos_entregues FROM pedidos p JOIN restaurantes r ON r.id = p.restaurante_id WHERE p.status = 'entregue' GROUP BY r.categoria ORDER BY ticket_medio DESC LIMIT 5
```
**Resultado da IA:**
```
('Pizza', 129.99, 1864)
('Japonesa', 107.42, 1661)
('Brasileira', 93.89, 1516)
('Mexicana', 90.73, 1699)
('Hambúrguer', 85.78, 1579)
```
**SQL de referência:**
```sql
SELECT r.categoria, ROUND(AVG(p.valor_total), 2) AS ticket_medio FROM pedidos p JOIN restaurantes r ON r.id = p.restaurante_id WHERE p.status = 'entregue' GROUP BY r.categoria ORDER BY ticket_medio DESC LIMIT 5
```
**Gabarito:**
```
('Pizza', 129.99)
('Japonesa', 107.42)
('Brasileira', 93.89)
('Mexicana', 90.73)
('Hambúrguer', 85.78)
```

### #6 ✅ Qual a nota média das avaliações de pedidos atrasados e de pedidos entregues no prazo?

**Explicação da IA:** Calcula a nota média das avaliações separando os pedidos entregues em atrasados (entrega depois da previsão) e no prazo. Considerei apenas pedidos entregues que têm avaliação; também mostro quantas avaliações há em cada grupo.

**SQL da IA:**
```sql
SELECT CASE WHEN p.data_entrega > p.previsao_entrega THEN 'atrasado' ELSE 'no_prazo' END AS situacao_entrega, ROUND(AVG(a.nota), 2) AS nota_media, COUNT(*) AS qtd_avaliacoes FROM pedidos p JOIN avaliacoes a ON a.pedido_id = p.id WHERE p.status = 'entregue' GROUP BY situacao_entrega
```
**Resultado da IA:**
```
('atrasado', 3.5, 1600)
('no_prazo', 4.38, 6392)
```
**SQL de referência:**
```sql
SELECT CASE WHEN p.data_entrega > p.previsao_entrega THEN 'atrasado' ELSE 'no prazo' END AS situacao, ROUND(AVG(a.nota), 2) AS nota_media FROM pedidos p JOIN avaliacoes a ON a.pedido_id = p.id WHERE p.status = 'entregue' GROUP BY situacao
```
**Gabarito:**
```
('atrasado', 3.5)
('no prazo', 4.38)
```

### #7 ✅ Quantos pedidos foram cancelados em cada mês de 2025?

**Explicação da IA:** Conta os pedidos com status 'cancelado' em cada mês de 2025, usando a data em que o pedido foi feito. Meses sem nenhum cancelamento não aparecem no resultado.

**SQL da IA:**
```sql
SELECT strftime('%Y-%m', data_pedido) AS mes, COUNT(*) AS pedidos_cancelados FROM pedidos WHERE status = 'cancelado' AND strftime('%Y', data_pedido) = '2025' GROUP BY mes ORDER BY mes
```
**Resultado da IA:**
```
('2025-01', 63)
('2025-02', 61)
('2025-03', 62)
('2025-04', 51)
('2025-05', 67)
... (12 linhas no total)
```
**SQL de referência:**
```sql
SELECT strftime('%Y-%m', data_pedido) AS mes, COUNT(*) AS cancelados FROM pedidos WHERE status = 'cancelado' AND strftime('%Y', data_pedido) = '2025' GROUP BY mes
```
**Gabarito:**
```
('2025-01', 63)
('2025-02', 61)
('2025-03', 62)
('2025-04', 51)
('2025-05', 67)
... (12 linhas no total)
```

### #8 ✅ Qual o tempo médio de entrega em minutos, considerando os pedidos entregues?

**Explicação da IA:** Calcula a média, em minutos, do tempo entre a hora do pedido e a hora real da entrega. Considerei apenas pedidos com status 'entregue'.

**SQL da IA:**
```sql
SELECT ROUND(AVG((julianday(data_entrega) - julianday(data_pedido)) * 24 * 60), 2) AS tempo_medio_entrega_min FROM pedidos WHERE status = 'entregue' AND data_entrega IS NOT NULL
```
**Resultado da IA:**
```
(37.31,)
```
**SQL de referência:**
```sql
SELECT ROUND(AVG((julianday(data_entrega) - julianday(data_pedido)) * 24 * 60), 2) AS tempo_medio_min FROM pedidos WHERE status = 'entregue'
```
**Gabarito:**
```
(37.31,)
```

### #9 ✅ Qual a taxa de atraso no horário de pico do jantar (18h às 21h) comparada com os outros horários?

**Explicação da IA:** Separa os pedidos entregues em dois grupos pela hora do pedido (18h a 21h, inclusive, versus o resto) e calcula a taxa de atraso de cada um. Pedidos cancelados ficam de fora da conta.

**SQL da IA:**
```sql
SELECT CASE WHEN CAST(strftime('%H', data_pedido) AS INTEGER) BETWEEN 18 AND 21 THEN 'Pico do jantar (18h-21h)' ELSE 'Outros horários' END AS periodo, COUNT(*) AS pedidos_entregues, SUM(CASE WHEN data_entrega > previsao_entrega THEN 1 ELSE 0 END) AS pedidos_atrasados, ROUND(100.0 * SUM(CASE WHEN data_entrega > previsao_entrega THEN 1 ELSE 0 END) / COUNT(*), 2) AS taxa_atraso_pct FROM pedidos WHERE status = 'entregue' GROUP BY periodo ORDER BY periodo
```
**Resultado da IA:**
```
('Outros horários', 5335, 488, 9.15)
('Pico do jantar (18h-21h)', 5964, 1785, 29.93)
```
**SQL de referência:**
```sql
SELECT CASE WHEN CAST(strftime('%H', data_pedido) AS INTEGER) BETWEEN 18 AND 21 THEN 'pico jantar' ELSE 'outros horários' END AS periodo, ROUND(100.0 * SUM(CASE WHEN data_entrega > previsao_entrega THEN 1 ELSE 0 END) / COUNT(*), 2) AS taxa_atraso_pct FROM pedidos WHERE status = 'entregue' GROUP BY periodo
```
**Gabarito:**
```
('outros horários', 9.15)
('pico jantar', 29.93)
```

### #10 ✅ Quais os 2 produtos mais vendidos em quantidade?

**Explicação da IA:** Soma a quantidade vendida de cada produto e mostra os 2 com maior total. Considerei apenas pedidos entregues, pois pedido cancelado não conta como venda.

**SQL da IA:**
```sql
SELECT i.produto, SUM(i.quantidade) AS quantidade_vendida FROM itens_pedido i JOIN pedidos p ON p.id = i.pedido_id WHERE p.status = 'entregue' GROUP BY i.produto ORDER BY quantidade_vendida DESC LIMIT 2
```
**Resultado da IA:**
```
('Pizza Quatro Queijos', 1352)
('Pizza Calabresa', 1339)
```
**SQL de referência:**
```sql
SELECT i.produto, SUM(i.quantidade) AS quantidade_vendida FROM itens_pedido i JOIN pedidos p ON p.id = i.pedido_id WHERE p.status = 'entregue' GROUP BY i.produto ORDER BY quantidade_vendida DESC LIMIT 2
```
**Gabarito:**
```
('Pizza Quatro Queijos', 1352)
('Pizza Calabresa', 1339)
```

### #11 ✅ Qual a participação (%) de cada forma de pagamento no total de pedidos?

**Explicação da IA:** Conta os pedidos de cada forma de pagamento e calcula a porcentagem de cada uma sobre o total de pedidos. Considerei todos os pedidos, inclusive os cancelados, porque a pergunta fala em total de pedidos e não em vendas.

**SQL da IA:**
```sql
SELECT forma_pagamento, COUNT(*) AS total_pedidos, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM pedidos), 2) AS participacao_pct FROM pedidos GROUP BY forma_pagamento ORDER BY participacao_pct DESC
```
**Resultado da IA:**
```
('cartao_credito', 5360, 44.67)
('pix', 4201, 35.01)
('cartao_debito', 1847, 15.39)
('dinheiro', 592, 4.93)
```
**SQL de referência:**
```sql
SELECT forma_pagamento, ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM pedidos), 2) AS participacao_pct FROM pedidos GROUP BY forma_pagamento
```
**Gabarito:**
```
('cartao_credito', 44.67)
('cartao_debito', 15.39)
('dinheiro', 4.93)
('pix', 35.01)
```

### #12 ✅ Quantos pedidos tiveram frete grátis?

**Explicação da IA:** Conta os pedidos com taxa de entrega igual a zero, que é o frete grátis (acontece quando os itens somam R$ 100 ou mais). A primeira coluna inclui todos os pedidos, inclusive cancelados. A segunda conta só os pedidos entregues.

**SQL da IA:**
```sql
SELECT COUNT(*) AS pedidos_frete_gratis, SUM(CASE WHEN status = 'entregue' THEN 1 ELSE 0 END) AS pedidos_frete_gratis_entregues FROM pedidos WHERE taxa_entrega = 0
```
**Resultado da IA:**
```
(4370, 4110)
```
**SQL de referência:**
```sql
SELECT COUNT(*) AS pedidos_frete_gratis FROM pedidos WHERE taxa_entrega = 0
```
**Gabarito:**
```
(4370,)
```

### #13 ✅ Qual o restaurante com mais pedidos entregues em Porto Alegre? Mostre o nome e a quantidade.

**Explicação da IA:** A consulta conta os pedidos com status 'entregue' de cada restaurante localizado em Porto Alegre e mostra o que tem mais. Considerei a cidade do restaurante, não a do cliente. Em caso de empate, aparece só um deles.

**SQL da IA:**
```sql
SELECT r.nome AS restaurante, COUNT(p.id) AS qtd_pedidos_entregues FROM pedidos p JOIN restaurantes r ON r.id = p.restaurante_id WHERE p.status = 'entregue' AND r.cidade = 'Porto Alegre' GROUP BY r.id, r.nome ORDER BY qtd_pedidos_entregues DESC LIMIT 1
```
**Resultado da IA:**
```
('Sabor do Chef (Hambúrguer)', 260)
```
**SQL de referência:**
```sql
SELECT r.nome, COUNT(*) AS pedidos_entregues FROM pedidos p JOIN restaurantes r ON r.id = p.restaurante_id WHERE p.status = 'entregue' AND r.cidade = 'Porto Alegre' GROUP BY r.id, r.nome ORDER BY pedidos_entregues DESC LIMIT 1
```
**Gabarito:**
```
('Sabor do Chef (Hambúrguer)', 260)
```

### #14 ✅ Quantos clientes diferentes fizeram pelo menos um pedido em dezembro de 2025?

**Explicação da IA:** Conta os clientes distintos que fizeram ao menos um pedido em dezembro de 2025, com base na data do pedido. Considerei todos os pedidos, inclusive os cancelados, pois a pergunta é sobre fazer um pedido.

**SQL da IA:**
```sql
SELECT COUNT(DISTINCT cliente_id) AS clientes_distintos FROM pedidos WHERE strftime('%Y-%m', data_pedido) = '2025-12'
```
**Resultado da IA:**
```
(746,)
```
**SQL de referência:**
```sql
SELECT COUNT(DISTINCT cliente_id) AS clientes_ativos FROM pedidos WHERE strftime('%Y-%m', data_pedido) = '2025-12'
```
**Gabarito:**
```
(746,)
```

### #15 ✅ Qual a distância média, em km, dos pedidos atrasados entregues de bicicleta?

**Explicação da IA:** Calcula a distância média, em km, dos pedidos atrasados feitos por entregadores de bicicleta. Considerei atrasado o pedido entregue depois da previsão de entrega. Também mostra quantos pedidos entraram na conta.

**SQL da IA:**
```sql
SELECT ROUND(AVG(p.distancia_km), 2) AS distancia_media_km, COUNT(*) AS pedidos_atrasados FROM pedidos p JOIN entregadores e ON e.id = p.entregador_id WHERE e.veiculo = 'bicicleta' AND p.status = 'entregue' AND p.data_entrega > p.previsao_entrega
```
**Resultado da IA:**
```
(5.53, 1548)
```
**SQL de referência:**
```sql
SELECT ROUND(AVG(p.distancia_km), 2) AS distancia_media_km FROM pedidos p JOIN entregadores e ON e.id = p.entregador_id WHERE p.status = 'entregue' AND p.data_entrega > p.previsao_entrega AND e.veiculo = 'bicicleta'
```
**Gabarito:**
```
(5.53,)
```

### #16 ✅ Qual a porcentagem de pedidos entregues que receberam avaliação?

**Explicação da IA:** A consulta calcula a porcentagem de pedidos com status 'entregue' que possuem uma avaliação registrada. Ela divide os entregues avaliados pelo total de entregues.

**SQL da IA:**
```sql
SELECT ROUND(100.0 * COUNT(a.pedido_id) / COUNT(p.id), 2) AS pct_entregues_avaliados FROM pedidos p LEFT JOIN avaliacoes a ON a.pedido_id = p.id WHERE p.status = 'entregue'
```
**Resultado da IA:**
```
(70.73,)
```
**SQL de referência:**
```sql
SELECT ROUND(100.0 * COUNT(a.pedido_id) / COUNT(*), 2) AS pct_avaliados FROM pedidos p LEFT JOIN avaliacoes a ON a.pedido_id = p.id WHERE p.status = 'entregue'
```
**Gabarito:**
```
(70.73,)
```

### #17 ✅ Qual entregador fez mais entregas em São Paulo? Mostre nome, veículo e quantidade.

**Explicação da IA:** Conta os pedidos entregues por cada entregador que atua em São Paulo e mostra quem tem a maior quantidade. Considerei apenas pedidos com status 'entregue' e a cidade do entregador. Se houver empate, todos os empatados aparecem.

**SQL da IA:**
```sql
WITH contagem AS (SELECT e.id, e.nome, e.veiculo, COUNT(p.id) AS quantidade_entregas FROM entregadores e JOIN pedidos p ON p.entregador_id = e.id WHERE e.cidade = 'São Paulo' AND p.status = 'entregue' GROUP BY e.id, e.nome, e.veiculo) SELECT nome, veiculo, quantidade_entregas FROM contagem WHERE quantidade_entregas = (SELECT MAX(quantidade_entregas) FROM contagem)
```
**Resultado da IA:**
```
('Tainá Teixeira', 'moto', 217)
```
**SQL de referência:**
```sql
SELECT e.nome, e.veiculo, COUNT(*) AS entregas FROM pedidos p JOIN entregadores e ON e.id = p.entregador_id WHERE p.status = 'entregue' AND e.cidade = 'São Paulo' GROUP BY e.id, e.nome, e.veiculo ORDER BY entregas DESC LIMIT 1
```
**Gabarito:**
```
('Tainá Teixeira', 'moto', 217)
```

### #18 ✅ Qual foi o salário médio dos entregadores em 2025?

**Explicação da IA:** O banco não tem informações de salário ou remuneração dos entregadores. A tabela de entregadores traz apenas nome, veículo e cidade, e os pedidos registram a taxa de entrega cobrada do cliente, não o valor pago ao entregador.

**SQL da IA:**
```sql
(nenhum)
```
**Resultado da IA:**
```
-
```
**SQL de referência:**
```sql
(sem resposta possível)
```
**Gabarito:**
```
-
```

