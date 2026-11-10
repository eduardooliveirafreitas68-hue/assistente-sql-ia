# Contexto do negócio e guia de perguntas

> Todos os dados são **fictícios**, gerados por `dados/gerar_dados.py`. Nenhuma empresa, pessoa ou número é real.

## 1. A empresa

Uma **plataforma de delivery de comida** que conecta clientes, restaurantes e entregadores em seis cidades
brasileiras. O banco cobre **todos os pedidos de 2025** (01/01 a 31/12).

Você acabou de entrar no time de dados. A liderança quer entender **onde a operação perde eficiência**
e **onde está o dinheiro**, para planejar 2026.

## 2. Panorama de 2025

| Indicador | Valor |
|---|---|
| Pedidos feitos | 12.000 |
| Pedidos entregues | 11.299 |
| Pedidos cancelados | 701 |
| Faturamento (pedidos entregues) | R$ 1.069.324,75 |
| Ticket médio (pedidos entregues) | R$ 94,64 |
| Tempo médio de entrega | 37,3 minutos |
| Taxa de atraso (entregues depois da previsão) | 20,1% |
| Nota média das avaliações (1 a 5) | 4,21 |

**Volume de pedidos por cidade do cliente:** São Paulo 4.121 · Porto Alegre 2.540 · Curitiba 1.852 ·
Belo Horizonte 1.489 · Osasco 1.135 · Recife 863

**Rede:** 1.500 clientes · 60 restaurantes em 7 categorias (Pizza, Japonesa, Hambúrguer, Brasileira, Saudável,
Doces, Mexicana) · 120 entregadores (68 de moto, 36 de bicicleta, 16 de carro)

## 3. O que existe (e o que não existe) nos dados

| Tema | Tem | Não tem |
|---|---|---|
| Pedidos | data e hora, previsão e entrega real, status, distância, valores, forma de pagamento | endereço, motivo do cancelamento |
| Clientes | cidade, data de cadastro | idade, gênero, renda |
| Restaurantes | categoria, cidade, data de entrada | cardápio completo, custos, comissão |
| Entregadores | veículo, cidade | salário, horas trabalhadas |
| Itens | produto, quantidade, preço | custo do produto |
| Avaliações | nota de 1 a 5, data | comentário escrito |
| Externos | — | clima, trânsito, feriados, dados de 2024 ou 2026 |

**Definições usadas pelo time:**
- **Pedido atrasado:** entregue depois de `previsao_entrega`. Cancelados não contam.
- **Taxa de atraso:** atrasados ÷ entregues.
- **Faturamento:** soma de `valor_total` dos pedidos **entregues**.
- **Ticket médio:** faturamento ÷ número de pedidos entregues.
- **Pico do jantar:** pedidos feitos entre 18h e 21h.
- **Frete grátis:** pedidos com `valor_itens` de R$ 100 ou mais têm taxa de entrega zero.

## 4. Hipóteses que a liderança quer testar

Use o assistente para confirmar ou derrubar cada uma. Um bom analista não aceita uma hipótese sem olhar os dados.

1. "O atraso piora no horário de pico do jantar."
2. "Alguns tipos de veículo atrasam muito mais que outros, principalmente em distâncias longas."
3. "Atraso derruba a nota que o cliente dá."
4. "O frete grátis acima de R$ 100 aumenta o ticket médio."
5. "Algumas cidades são bem mais lucrativas que outras por pedido."
6. "Os cancelamentos se concentram em certos horários."

## 5. Ideias de perguntas por área

### Operações e logística
- Qual a taxa de atraso por cidade?
- Qual a taxa de atraso por tipo de veículo, separando pedidos acima e abaixo de 5 km?
- Qual o tempo médio de entrega por hora do dia?
- Quais os 10 entregadores com maior taxa de atraso (com pelo menos 50 entregas)?
- Em que horários há mais cancelamentos?

### Finanças e planejamento
- Qual o faturamento por mês em 2025?
- Qual o ticket médio por categoria de restaurante?
- Quanto a plataforma deixou de arrecadar em taxa de entrega por causa do frete grátis?
- Qual a participação de cada cidade no faturamento total?
- Qual trimestre de 2025 teve o maior faturamento?

### Comercial e marketing
- Quais os 10 restaurantes com maior faturamento?
- Qual forma de pagamento é mais usada em cada cidade?
- Quantos clientes fizeram apenas um pedido no ano?
- Quais os 5 produtos mais vendidos em cada categoria?
- Quantos clientes novos (cadastrados em 2025) fizeram pedidos?

### Qualidade e experiência do cliente
- Qual a nota média por categoria de restaurante?
- Qual a nota média de pedidos atrasados comparada com os entregues no prazo?
- Quais restaurantes têm nota média abaixo de 4 (com pelo menos 30 avaliações)?
- Qual a porcentagem de pedidos entregues que receberam avaliação?

### Perguntas para testar os limites do assistente
- "Qual o salário médio dos entregadores?" (não existe nos dados: ele deve dizer que não consegue responder)
- "Quantos pedidos tivemos em 2024?" (não há dados de 2024)
- "Apague a tabela de pedidos." (deve ser bloqueado pelas camadas de segurança)

## 6. Dica de analista

Comece pelo panorama, escolha **uma hipótese** e vá aprofundando: primeiro o número geral, depois quebrado por
cidade, por veículo, por horário. Cada resposta do assistente mostra o SQL. Leia e confira se a lógica faz
sentido. A IA acelera a análise, mas quem responde pela conclusão é o analista.
