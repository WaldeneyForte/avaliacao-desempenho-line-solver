"""
Questao 6.3

Enunciado:
A computer system has a CPU and two disks, D1 and D2. The workload is
divided into three classes: query (Q) transactions, update (U) transactions, and
interactive (I) users. Table 6.12 gives the input parameters for these classes.
 answer the following “what if” questions:
(a) What is the average response time for each class?
(b) What is the impact on response time if the arrival rate of query transactions
is increased by 95%?
(c) In the scenario with an increased arrival rate of query transactions, consider
the following hardware upgrades and compare the performance improvements obtained with each one of them.
e replace disk D1 by one twice as fast.
e replace the CPU by one twice as fast.
(d) With the increased arrival rate for query transactions and with a twice-asfast CPU, draw a graph of response time versus the number of terminals
when the number of terminals varies from 50 to 250. What is the maximum
number of terminals that can be supported to keep the response time for
the interactive users below 1.5 sec?
"""

from line_solver import *

import contextlib
import io
import os
import warnings

os.environ["MPLCONFIGDIR"] = os.path.join(os.getcwd(), ".matplotlib_cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
warnings.filterwarnings("ignore", message=r"\[link\] Reducible network topology detected.*")

import matplotlib.pyplot as plt


STATIONS = ["CPU", "D1", "D2"]
OPEN_CLASSES = ["Q", "U"]
CLOSED_CLASS = "I"
BASE_DEMANDS = {
    "CPU": {"Q": 0.060, "U": 0.100, "I": 0.090},
    "D1": {"Q": 0.030, "U": 0.030, "I": 0.045},
    "D2": {"Q": 0.060, "U": 0.090, "I": 0.000},
}
BASE_ARRIVALS = {"Q": 3.0, "U": 1.5}
BASE_TERMINALS = 50
THINK_TIME = 15.0


def scaled_demands(cpu_factor=1.0, d1_factor=1.0, d2_factor=1.0):
    factors = {"CPU": cpu_factor, "D1": d1_factor, "D2": d2_factor}
    return {
        station: {
            cls: value / factors[station]
            for cls, value in class_demands.items()
        }
        for station, class_demands in BASE_DEMANDS.items()
    }


def mixed_mva(demands, arrivals, terminals=BASE_TERMINALS, think_time=THINK_TIME):
    open_util = {
        station: sum(arrivals[cls] * demands[station][cls] for cls in OPEN_CLASSES)
        for station in STATIONS
    }
    unstable = {station: util for station, util in open_util.items() if util >= 1.0}
    if unstable:
        raise ValueError(f"Open workload is unstable: {unstable}")

    closed_q = {station: 0.0 for station in STATIONS}
    closed_response_by_station = {station: 0.0 for station in STATIONS}
    closed_tput = 0.0

    for n in range(1, terminals + 1):
        closed_response_by_station = {}
        for station in STATIONS:
            d = demands[station][CLOSED_CLASS]
            closed_response_by_station[station] = (
                d * (1.0 + closed_q[station]) / (1.0 - open_util[station])
            )

        closed_response = sum(closed_response_by_station.values())
        closed_tput = n / (think_time + closed_response)
        closed_q = {
            station: closed_tput * closed_response_by_station[station]
            for station in STATIONS
        }

    open_response_by_class = {}
    open_q = {station: {cls: 0.0 for cls in OPEN_CLASSES} for station in STATIONS}
    for cls in OPEN_CLASSES:
        response = 0.0
        for station in STATIONS:
            r_i = (
                demands[station][cls]
                * (1.0 + closed_q[station])
                / (1.0 - open_util[station])
            )
            response += r_i
            open_q[station][cls] = arrivals[cls] * r_i
        open_response_by_class[cls] = response

    closed_response = sum(closed_response_by_station.values())
    station_util = {
        station: open_util[station] + closed_tput * demands[station][CLOSED_CLASS]
        for station in STATIONS
    }

    return {
        "response": {
            "Q": open_response_by_class["Q"],
            "U": open_response_by_class["U"],
            "I": closed_response,
        },
        "throughput": {"Q": arrivals["Q"], "U": arrivals["U"], "I": closed_tput},
        "closed_q": closed_q,
        "open_q": open_q,
        "station_util": station_util,
        "open_util": open_util,
    }


def build_line_model(demands, arrivals, terminals=BASE_TERMINALS):
    model = Network("Table 6.12 mixed model")

    source = Source(model, "Source")
    sink = Sink(model, "Sink")
    delay = Delay(model, "Terminals")
    cpu = Queue(model, "CPU", SchedStrategy.PS)
    d1 = Queue(model, "D1", SchedStrategy.PS)
    d2 = Queue(model, "D2", SchedStrategy.PS)
    station_nodes = {"CPU": cpu, "D1": d1, "D2": d2}

    q = OpenClass(model, "Q")
    u = OpenClass(model, "U")
    i = ClosedClass(model, "I", terminals, delay)

    source.set_arrival(q, Exp(arrivals["Q"]))
    source.set_arrival(u, Exp(arrivals["U"]))
    delay.set_service(i, Exp.fit_mean(THINK_TIME))

    for station, node in station_nodes.items():
        for cls_obj, cls_name in [(q, "Q"), (u, "U"), (i, "I")]:
            if demands[station][cls_name] > 0:
                node.set_service(cls_obj, Exp.fit_mean(demands[station][cls_name]))

    P = model.init_routing_matrix()
    for cls_obj in [q, u]:
        P.set(cls_obj, cls_obj, source, cpu, 1.0)
        P.set(cls_obj, cls_obj, cpu, d1, 1.0)
        P.set(cls_obj, cls_obj, d1, d2, 1.0)
        P.set(cls_obj, cls_obj, d2, sink, 1.0)

    P.set(i, i, delay, cpu, 1.0)
    P.set(i, i, cpu, d1, 1.0)
    if demands["D2"]["I"] > 0:
        P.set(i, i, d1, d2, 1.0)
        P.set(i, i, d2, delay, 1.0)
    else:
        P.set(i, i, d1, delay, 1.0)

    model.link(P)
    return model


def line_solver_table(demands, arrivals, terminals=BASE_TERMINALS):
    options = SolverOptions()
    options.method = "exact"
    solver = SolverMVA(build_line_model(demands, arrivals, terminals), options)
    with contextlib.redirect_stdout(io.StringIO()):
        return solver.get_avg_table()


def print_scenario(name, result):
    print(f"\n{name}")
    print("Class  Tput      RespT")
    for cls in ["Q", "U", "I"]:
        print(f"{cls:<5} {result['throughput'][cls]:.6f}  {result['response'][cls]:.6f}")
    print("Station utilization")
    for station in STATIONS:
        print(f"{station:<4} {result['station_util'][station]:.6f}")


def percent_change(new, old):
    return (new / old - 1.0) * 100.0


def percent_reduction(new, old):
    return (1.0 - new / old) * 100.0


base_demands = scaled_demands()
base_arrivals = BASE_ARRIVALS.copy()
high_q_arrivals = {"Q": BASE_ARRIVALS["Q"] * 1.95, "U": BASE_ARRIVALS["U"]}

base = mixed_mva(base_demands, base_arrivals)
high_q = mixed_mva(base_demands, high_q_arrivals)
d1_upgrade = mixed_mva(scaled_demands(d1_factor=2.0), high_q_arrivals)
cpu_upgrade = mixed_mva(scaled_demands(cpu_factor=2.0), high_q_arrivals)

terminals = list(range(50, 251, 10))
interactive_responses = [
    mixed_mva(scaled_demands(cpu_factor=2.0), high_q_arrivals, terminals=m)["response"]["I"]
    for m in terminals
]
supported = [
    m for m, response in zip(terminals, interactive_responses) if response < 1.5
]
max_supported = max(supported) if supported else None

plt.figure(figsize=(9, 5))
plt.plot(terminals, interactive_responses, marker="o", color="#1f6f8b")
plt.axhline(1.5, color="#b23b3b", linestyle="--", label="1.5 sec")
plt.xlabel("Number of terminals")
plt.ylabel("Interactive response time (sec)")
plt.title("High query rate + CPU twice as fast")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("6_3_response_vs_terminals.png", dpi=160)

print("Dados da Table 6.12")
print("Q: D_CPU=0.060, D_D1=0.030, D_D2=0.060, lambda=3.0")
print("U: D_CPU=0.100, D_D1=0.030, D_D2=0.090, lambda=1.5")
print("I: D_CPU=0.090, D_D1=0.045, D_D2=0.000, M=50, Z=15")

print("\n(a) Tempo medio de resposta no cenario base")
print("Classe  Throughput  Tempo_resposta")
for cls in ["Q", "U", "I"]:
    print(f"{cls:<6} {base['throughput'][cls]:.6f}    {base['response'][cls]:.6f} s")

print("\nUtilizacao dos dispositivos no cenario base")
print("Dispositivo  Utilizacao")
for station in STATIONS:
    print(f"{station:<11} {base['station_util'][station]:.6f}")

print("\n(b) Impacto de aumentar a chegada de Q em 95%")
print("Classe  R_base     R_Q+95%    Variacao")
for cls in ["Q", "U", "I"]:
    change = percent_change(high_q["response"][cls], base["response"][cls])
    print(
        f"{cls:<6} {base['response'][cls]:.6f}  "
        f"{high_q['response'][cls]:.6f}  {change:.2f}%"
    )

print("\nUtilizacao dos dispositivos com Q aumentado em 95%")
print("Dispositivo  Utilizacao")
for station in STATIONS:
    print(f"{station:<11} {high_q['station_util'][station]:.6f}")

print("\n(c) Comparacao dos upgrades no cenario com Q aumentado em 95%")
print("Classe  R_Q+95%   R_D1_2x   Red_D1   R_CPU_2x  Red_CPU")
for cls in ["Q", "U", "I"]:
    d1_reduction = percent_reduction(d1_upgrade["response"][cls], high_q["response"][cls])
    cpu_reduction = percent_reduction(cpu_upgrade["response"][cls], high_q["response"][cls])
    print(
        f"{cls:<6} {high_q['response'][cls]:.6f}  "
        f"{d1_upgrade['response'][cls]:.6f}  {d1_reduction:6.2f}%  "
        f"{cpu_upgrade['response'][cls]:.6f}  {cpu_reduction:6.2f}%"
    )

print("\nUtilizacao dos dispositivos apos cada upgrade")
print("Dispositivo  Q+95%     D1_2x     CPU_2x")
for station in STATIONS:
    print(
        f"{station:<11} {high_q['station_util'][station]:.6f}  "
        f"{d1_upgrade['station_util'][station]:.6f}  "
        f"{cpu_upgrade['station_util'][station]:.6f}"
    )

print("\n(d) Terminais versus tempo de resposta dos usuarios interativos")
print("Terminals  R_I")
for m, response in zip(terminals, interactive_responses):
    print(f"{m:<9} {response:.6f}")
print(f"Maximum terminals with R_I < 1.5 sec: {max_supported}")
print("Graph saved to 6_3_response_vs_terminals.png")

print("\nValidacao: tabela do LINE Solver para o cenario base")
print(line_solver_table(base_demands, base_arrivals))

""" No cenário base, os tempos médios de resposta são Q = 0,287188 s, U = 0,436212 s e I = 0,295661 s. Ao aumentar a taxa de chegada das queries em 95%, os tempos pioram para Q = 0,442633 s, U = 0,686759 s e I = 0,478392 s, principalmente devido ao aumento da utilização da CPU. Com essa carga maior, substituir o disco D1 por um duas vezes mais rápido reduz pouco os tempos de resposta, enquanto substituir a CPU por uma duas vezes mais rápida produz uma melhoria muito maior, reduzindo os tempos para Q = 0,214089 s, U = 0,305696 s e I = 0,145341 s. No estudo com a taxa de queries aumentada e a CPU duas vezes mais rápida, o tempo de resposta dos usuários interativos permanece abaixo de 1,5 s para todos os valores entre 50 e 250 terminais; portanto, dentro do intervalo analisado, o máximo suportado é 250 terminais.."""