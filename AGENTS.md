# AGENTS.md — Instruções para exercícios de Avaliação de Desempenho com LINE Solver

Este projeto contém exercícios de Avaliação de Desempenho resolvidos em Python com a biblioteca LINE Solver.

O objetivo é receber o número da questão e o enunciado, modelar o sistema corretamente, gerar um arquivo Python com o nome da questão, executar o código e produzir uma interpretação textual da saída.

## 1. Estrutura do projeto

A estrutura principal do projeto é:

```text
Avaliação de desempenho/
│
├── AGENTS.md
│
├── Docs/
│   ├── manual
│   └── motivacional
│
├── 5_3.py
├── 5_4.py
├── 5_5.py
└── ...
```

A pasta `Docs/` contém materiais de apoio:

* `manual`: manual ou resumo do manual do LINE Solver.
* `motivacional`: problema motivacional usado como referência, caso alguma questão dependa dele.

Nem todos os exercícios serão baseados no problema motivacional. Portanto, não assuma que toda questão usa o problema motivacional. Consulte o arquivo `Docs/motivacional` apenas quando o usuário disser que a questão depende do problema motivador, quando o enunciado mencionar explicitamente o problema motivacional, ou quando for necessário comparar com ele.

## 2. Entrada esperada do usuário

O usuário informará normalmente:

1. o número da questão, por exemplo: `5.3`, `5.4`, `6.1`;
2. o enunciado da questão;
3. possivelmente alguma instrução adicional do professor.

Exemplo:

```text
Questão 5.3:
[enunciado da questão]
```

A partir disso, gere um arquivo Python com o nome baseado no número da questão.

Exemplos:

```text
5.3  ->  5_3.py
5.4  ->  5_4.py
6.1  ->  6_1.py
7.10 ->  7_10.py
```

Não use nomes como `questao_5_3.py` ou `exercicio_5_3.py`, salvo se o usuário pedir. O padrão do projeto é usar apenas o número com ponto substituído por underline.

## 3. Formato obrigatório do arquivo Python

Todo arquivo Python gerado deve começar com o enunciado completo da questão como comentário.

Depois do enunciado, escreva o código.

Modelo obrigatório:

```python
"""
Questão 5.3

Enunciado:
[colar aqui o enunciado completo informado pelo usuário]
"""

from line_solver import *

# código da solução abaixo
```

O enunciado deve aparecer antes de qualquer import.

Não remova o enunciado do arquivo depois de gerar o código.

## 4. Biblioteca usada

A biblioteca principal é o LINE Solver.

Use preferencialmente:

```python
from line_solver import *
```

Se necessário, também é aceitável usar imports explícitos:

```python
from line_solver import Network, Queue, ClosedClass, SchedStrategy, Exp, SolverMVA
```

Se houver dúvida sobre sintaxe, consulte primeiro:

```text
Docs/manual
```

Se o arquivo `Docs/manual` estiver incompleto ou difícil de interpretar, use os exemplos já existentes nos arquivos `.py` do projeto.

## 5. Processo de resolução

Para cada questão, siga este fluxo:

1. Leia cuidadosamente o número e o enunciado da questão.
2. Identifique se o modelo é uma rede aberta, fechada ou mista.
3. Identifique os recursos do sistema: CPU, discos, servidores, filas, terminais, usuários etc.
4. Identifique os tempos de serviço, demandas, visitas, probabilidades de roteamento e população.
5. Consulte `Docs/manual` se precisar verificar a sintaxe do LINE Solver.
6. Consulte `Docs/motivacional` apenas se a questão depender explicitamente do problema motivador.
7. Crie o arquivo Python com nome baseado no número da questão.
8. Coloque o enunciado completo como comentário no início do arquivo.
9. Escreva o código usando LINE Solver.
10. Execute o arquivo.
11. Verifique se a saída faz sentido.
12. Responda ao usuário com um parágrafo interpretando a saída.

## 6. Regras de modelagem

### 6.1 Redes fechadas

Use `ClosedClass` quando o sistema tiver uma população fixa de usuários, clientes, processos ou jobs.

Exemplo:

```python
users = ClosedClass(model, "Users", 2, cpu)
```

Use redes fechadas quando o enunciado disser coisas como:

* número fixo de usuários no sistema;
* sempre existem N usuários ativos;
* quando um usuário sai, outro entra;
* sistema com multiprogramação fixa;
* população fechada.

### 6.2 Redes abertas

Se o enunciado especificar taxa externa de chegada, por exemplo jobs por segundo, clientes por minuto ou requisições por hora, considere uma rede aberta.

Nesse caso, consulte o manual do LINE Solver para usar a classe e a configuração adequadas.

Não transforme uma rede aberta em fechada sem justificativa.

### 6.3 Estações de serviço

Dispositivos como CPU, discos, servidores e recursos computacionais geralmente devem ser modelados como filas.

Para atendimento FCFS, use:

```python
station = Queue(model, "Nome", SchedStrategy.FCFS)
```

Exemplo:

```python
cpu = Queue(model, "CPU", SchedStrategy.FCFS)
disk = Queue(model, "Disk", SchedStrategy.FCFS)
```

Use outro escalonamento apenas se o enunciado especificar.

### 6.4 Tempos médios de serviço

Para tempos médios de serviço, use:

```python
station.set_service(classe, Exp.fit_mean(valor))
```

Exemplo:

```python
cpu.set_service(users, Exp.fit_mean(10.0))
```

Mantenha as unidades consistentes. Se o enunciado usa segundos, mantenha tudo em segundos. Se usa minutos, mantenha tudo em minutos ou converta tudo claramente.

### 6.5 Roteamento

Use matriz de roteamento quando houver probabilidades de transição entre dispositivos.

Exemplo:

```python
P = model.init_routing_matrix()

P.set(users, users, cpu, disk1, 0.5)
P.set(users, users, cpu, disk2, 0.5)
P.set(users, users, disk1, cpu, 1.0)
P.set(users, users, disk2, cpu, 1.0)

model.link(P)
```

Verifique sempre se as probabilidades de saída de uma estação somam 1 quando isso for necessário.

## 7. Solver

Para redes fechadas simples, use preferencialmente:

```python
solver = SolverMVA(model)
print(solver.get_avg_table())
```

Se a questão exigir outro tipo de solver, consulte `Docs/manual`.

Não invente resultados. Execute o código antes de comentar a saída.

## 8. Interpretação da saída

A saída do LINE Solver pode conter colunas como:

```text
Station
JobClass
QLen
Util
RespT
ResidT
ArvR
Tput
```

Interprete assim:

* `Station`: dispositivo ou estação.
* `JobClass`: classe de jobs ou usuários.
* `QLen`: número médio de jobs na estação, incluindo quem está em serviço e quem está esperando.
* `Util`: utilização do recurso.
* `RespT`: tempo médio de resposta na estação, incluindo espera e serviço.
* `ResidT`: tempo residual médio.
* `ArvR`: taxa média de chegada.
* `Tput`: throughput da estação.

Em redes fechadas, a soma dos valores de `QLen` deve ser aproximadamente igual à população total do sistema.

## 9. Resposta ao usuário

Depois de gerar e executar o código, responda com:

1. nome do arquivo criado;
2. confirmação de que o código foi gerado;
3. parágrafo interpretativo da saída.

O parágrafo deve ser em português, claro e adequado para entrega acadêmica.

O parágrafo deve comentar, quando aplicável:

* utilização;
* throughput;
* tamanho médio de fila;
* tempo médio de resposta;
* gargalo;
* comparação com outro cenário;
* conclusão sobre o desempenho.

Exemplo de estilo:

```text
A saída mostra que o dispositivo com maior utilização é o disco lento, indicando que ele é o principal gargalo do sistema. A CPU apresenta utilização moderada, enquanto o disco rápido possui menor tempo médio de resposta. O maior tamanho médio de fila e o maior tempo médio de resposta aparecem no disco lento, o que indica maior concentração de espera nesse recurso. Como a soma dos tamanhos médios de fila é compatível com a população do sistema, os resultados são consistentes com o modelo fechado descrito no enunciado.
```

Quando o professor pedir apenas um parágrafo, responda com apenas um parágrafo de interpretação.

## 10. Validação dos resultados

Antes de concluir, verifique:

* o script executa sem erro;
* o arquivo tem o nome correto da questão;
* o enunciado está comentado no início do arquivo;
* os tempos usam unidades consistentes;
* as probabilidades de roteamento estão corretas;
* em redes fechadas, a soma dos `QLen` bate aproximadamente com a população;
* o gargalo identificado é coerente com os valores de utilização, fila e tempo de resposta;
* o comentário textual está baseado na saída real do código.

## 11. Erros comuns

Se ocorrer:

```text
ModuleNotFoundError: No module named 'line_solver'
```

instale o pacote no mesmo Python usado para executar o script:

```powershell
python -m pip install line-solver
```

Se estiver usando um interpretador específico, instale com ele:

```powershell
& "C:\Users\dedey\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pip install line-solver
```

Não assuma que um pacote instalado no Anaconda estará disponível em outro Python.

## 12. Regras importantes

Não assuma que toda questão é baseada no problema 5.3.

Não use `Docs/motivacional` a menos que a questão peça ou dependa dele.

Não sobrescreva arquivos de questões antigas sem necessidade.

Não mude a estrutura do projeto.

Não crie pastas extras sem pedir.

Não gere explicações excessivamente longas se o usuário pediu apenas o parágrafo final.

Não invente números.

Em caso de dúvida sobre a interpretação do enunciado, explique a dúvida e, se possível, gere uma solução assumindo explicitamente a hipótese usada.
