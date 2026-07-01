# Avaliação de Desempenho com LINE Solver

Repositório com exercícios resolvidos de **Avaliação de Desempenho** usando Python e a biblioteca **LINE Solver** para modelagem e análise de sistemas de filas.

## 📋 Sobre o Projeto

Este projeto implementa soluções para problemas de avaliação de desempenho de sistemas computacionais, utilizando **Redes de Filas Markovianas (Markovian Queueing Networks)** e o software **LINE Solver** para análise de performance.

### Tópicos cobertos:

- ✅ Sistemas em estado estacionário
- ✅ Redes fechadas (closed queueing networks)
- ✅ Redes abertas (open queueing networks)
- ✅ Cálculo de utilização, throughput, tempo de resposta
- ✅ Identificação de gargalos
- ✅ Análise de sensibilidade
- ✅ Múltiplas classes de jobs
- ✅ Roteamento probabilístico

## 📁 Estrutura do Projeto

```
avaliacao-desempenho-line-solver/
│
├── README.md                    # Este arquivo
├── AGENTS.md                    # Instruções para resolução de exercícios
│
├── docs/                        # Documentação e materiais de apoio
│   ├── manual                   # Manual/resumo do LINE Solver
│   └── motivacional             # Problema motivacional de referência
│
├── Questões Capítulo 5/
│   ├── 5_3.py                   # Desempenho de sistema workstation original
│   ├── 5_4.py                   # Estudo de cenários com diferentes configurações
│   ├── 5_5.py                   # Análise comparativa
│   ├── 5_6.py                   # Efeitos de mudanças de parâmetros
│   ├── 5_7.py                   # Multiprogramação e limites de performance
│   ├── 5_8.py                   # Variações de carga
│   ├── 5_15.py                  # Análise avançada
│   ├── 5_16.py                  # Cenários complexos
│   └── 5_17.py                  # Bounds e limitações
│       └── 5_17_bounds.png      # Gráfico de resultados
│
├── Questões Capítulo 6/
│   ├── 6_1.py                   # Sistema com múltiplos recursos
│   ├── 6_2.py                   # Redes abertas com taxa de chegada
│   └── 6_3.py                   # Análise de sensibilidade (terminais)
│       └── 6_3_response_vs_terminals.png  # Gráfico de resposta
│
└── Questões Capítulo 7/
    ├── 7_1.py                   # Modelo com classes de jobs
    ├── 7_2.py                   # Análise multiclasse
    │   └── 7_2_response_vs_terminals.png  # Gráfico de resposta
    ├── 7_4.py                   # Roteamento dinâmico
    └── 7_7.py                   # Cenários complexos
```

## 🚀 Como Usar

### Pré-requisitos

- **Python 3.7+**
- **LINE Solver**

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/WaldeneyForte/avaliacao-desempenho-line-solver.git
cd avaliacao-desempenho-line-solver
```

2. Instale a biblioteca LINE Solver:
```bash
pip install line-solver
```

### Executando um Exercício

Para rodar qualquer um dos exercícios:

```bash
python 5_3.py
```

A saída exibirá uma tabela com as métricas de desempenho:

```
            Station  JobClass    QLen      Util      RespT  ...
0               CPU     Users  0.84485  0.424242  19.84515  ...
1          FastDisk     Users  0.65657  0.328283  19.84848  ...
2           SlowDisk     Users  0.49858  0.249292  19.95454  ...
```

## 📊 Métricas de Saída

A análise de cada exercício gera as seguintes métricas:

| Métrica | Descrição |
|---------|-----------|
| **Station** | Dispositivo ou estação de serviço (CPU, disco, etc.) |
| **JobClass** | Classe de jobs ou usuários do sistema |
| **QLen** | Número médio de jobs na fila (incluindo em serviço) |
| **Util** | Taxa de utilização do recurso (0-1) |
| **RespT** | Tempo médio de resposta na estação |
| **ResidT** | Tempo residual médio |
| **ArvR** | Taxa média de chegada de jobs |
| **Tput** | Throughput (taxa de saída de jobs completados) |

## 📖 Estrutura dos Arquivos de Exercício

Cada arquivo `.py` segue um padrão:

```python
"""
Questão 5.3

Enunciado:
[Descrição completa do problema]
"""

from line_solver import *

# Criação do modelo
model = Network("Nome do Sistema")

# Definição de estações (filas)
cpu = Queue(model, "CPU", SchedStrategy.FCFS)

# Definição de classes de jobs
users = ClosedClass(model, "Users", 2, cpu)

# Configuração de tempos de serviço
cpu.set_service(users, Exp.fit_mean(10.0))

# Definição de roteamento
P = model.init_routing_matrix()
# ... configurar transições ...
model.link(P)

# Resolução
solver = SolverMVA(model)
print(solver.get_avg_table())

# Interpretação dos resultados
```

## 🔧 Solvers Disponíveis

O LINE Solver oferece diferentes solvers para diferentes tipos de sistemas:

- **SolverMVA**: Algoritmo de Análise de Valor Médio (Mean Value Analysis)
  - Ideal para redes fechadas simples
  - Cálculo rápido de métricas de estado estacionário

- **SolverJMT**: Integração com JMVA
  - Suporta simulação e análise analítica
  - Mais flexível para sistemas complexos

## 📝 Conceitos-chave

### Redes Fechadas (Closed Networks)
- População fixa de usuários/jobs
- Nenhuma chegada ou saída externa
- Exemplo: Sistema com N terminais/processadores

```python
users = ClosedClass(model, "Users", 2, cpu)  # 2 usuários sempre no sistema
```

### Redes Abertas (Open Networks)
- Taxa externa de chegada de jobs
- Jobs podem chegar e partir livremente
- Exemplo: Servidor web com requisições externas

### Roteamento Probabilístico
- Jobs transitam entre estações com probabilidades definidas
- Matriz de roteamento especifica transições

## 🎯 Objetivos de Aprendizado

Após trabalhar com estes exercícios, você compreenderá:

1. Como modelar sistemas computacionais como redes de filas
2. Calcular métricas de desempenho (utilização, throughput, tempo de resposta)
3. Identificar gargalos em sistemas
4. Realizar análise de sensibilidade
5. Comparar diferentes cenários e configurações
6. Usar ferramentas de análise para orientar decisões de design

## 📚 Referências

- **AGENTS.md**: Instruções detalhadas para resolução de exercícios
- **docs/manual**: Manual técnico do LINE Solver
- **docs/motivacional**: Problema motivacional de referência

## 💡 Dicas de Uso

1. **Comece simples**: Inicie com 5_3.py para entender a sintaxe
2. **Compare cenários**: Execute e compare diferentes configurações
3. **Verifique a física**: Valide se os resultados fazem sentido
4. **Use os gráficos**: Visualize tendências com os gráficos PNG fornecidos
5. **Consulte AGENTS.md**: Refer-se às instruções para dúvidas

## 🐛 Erros Comuns

### `ModuleNotFoundError: No module named 'line_solver'`

Instale o pacote:
```bash
python -m pip install line-solver
```

Se usar interpretador específico:
```bash
"C:\caminho\para\python.exe" -m pip install line-solver
```

### Soma de QLen ≠ População

Verifique se:
- A matriz de roteamento está correta
- As probabilidades de transição somam 1
- Não há perda de jobs no roteamento

## 👨‍💻 Autor

**Waldeneya Forte** - [GitHub](https://github.com/WaldeneyForte)

## 📄 Licença

Este projeto é de código aberto e disponível para fins educacionais.

## 🤝 Contribuições

Sugestões e melhorias são bem-vindas! Abra uma issue ou um pull request.

---

**Última atualização**: Julho de 2026

Para instruções sobre como adicionar novos exercícios, consulte **AGENTS.md**.
