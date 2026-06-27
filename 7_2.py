"""
Questao 7.2

Enunciado:
An interactive computer system has M terminals used for a data-entry application. This application presents the user with a screen to be filled out before submitting it to the mainframe for processing. The computing system has one CPU and two disks. The results of measurements taken during a 1 hour interval
are shown in Table 7.7.
Main memory at the mainframe is such that at most 5 transactions may be
executed simultaneously. The company intends to redesign the user interface
to increase the productivity at each terminal so that the average think time may
be reduced to 60% of its original value. Also, the company expects that the
recovery of the economy will boost its business so that more terminals will be
needed. Under this new scenario, determine the maximum number of terminals,
Mmax, the system will be able to handle before response time exceeds 3 sec.
Plot a response time versus number of terminals curve. When the number
of terminals is equal to Mmax, how much of the transaction response time is
spent in the computer system, and how much is spent queuing for memory?
Compute the CPU and disk utilizations. What would be your recommendation
for allowing the system to handle 1.2 x Mpax terminals while keeping the average
response time at 3 sec? Justify your answer by using your model. In answering
the questions above you should use MVA. To take memory queuing into account
you should use MVA with load-dependent devices.
"""

from line_solver import *

import contextlib
from io import StringIO
import os
import warnings

import matplotlib.pyplot as plt
import numpy as np


os.environ["MPLCONFIGDIR"] = os.path.join(os.getcwd(), ".matplotlib_cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
warnings.filterwarnings("ignore", message=r"\[link\] Reducible network topology detected.*")


COMPLETIONS_PER_HOUR = 11808
OBSERVATION_SECONDS = 3600
BASE_TERMINALS = 100
BASE_RESPONSE = 0.47
BASE_UTIL = {
    "CPU": 0.26,
    "Disk1": 0.41,
    "Disk2": 0.33,
}
MEMORY_LIMIT = 5
RESPONSE_LIMIT = 3.0

BASE_THROUGHPUT = COMPLETIONS_PER_HOUR / OBSERVATION_SECONDS
BASE_THINK_TIME = BASE_TERMINALS / BASE_THROUGHPUT - BASE_RESPONSE
NEW_THINK_TIME = 0.60 * BASE_THINK_TIME
BASE_DEMANDS = {
    station: util / BASE_THROUGHPUT
    for station, util in BASE_UTIL.items()
}


def solve_line_table(model, solver_class=SolverMVA, method="exact"):
    options = SolverOptions()
    options.method = method
    solver = solver_class(model, options)
    with contextlib.redirect_stdout(StringIO()):
        return solver.get_avg_table()


def build_central_model(population, demands):
    model = Network(f"Central subsystem N={population}")
    cpu = Queue(model, "CPU", SchedStrategy.FCFS)
    disk1 = Queue(model, "Disk1", SchedStrategy.FCFS)
    disk2 = Queue(model, "Disk2", SchedStrategy.FCFS)
    transactions = ClosedClass(model, "Transactions", population, cpu)

    cpu.set_service(transactions, Exp.fit_mean(demands["CPU"]))
    disk1.set_service(transactions, Exp.fit_mean(demands["Disk1"]))
    disk2.set_service(transactions, Exp.fit_mean(demands["Disk2"]))

    model.link(Network.serialRouting(cpu, disk1, disk2))
    return model


def central_results(demands, memory_limit):
    results = {0: {"throughput": 0.0, "response": 0.0, "util": {s: 0.0 for s in demands}}}
    for population in range(1, memory_limit + 1):
        table = solve_line_table(build_central_model(population, demands))
        throughput = float(table.data.loc[table.data["Station"] == "CPU", "Tput"].iloc[0])
        response = float(table.data["RespT"].astype(float).sum())
        util = {
            station: float(table.data.loc[table.data["Station"] == station, "Util"].iloc[0])
            for station in demands
        }
        results[population] = {
            "throughput": throughput,
            "response": response,
            "util": util,
        }
    return results


def build_load_dependent_line_model(terminals, think_time, central):
    model = Network(f"Memory-limited model M={terminals}")
    terminal = Delay(model, "Terminals")
    computer = Queue(model, "Memory-limited computer", SchedStrategy.FCFS)
    users = ClosedClass(model, "Users", terminals, terminal)

    base_rate = central[1]["throughput"]
    terminal.set_service(users, Exp.fit_mean(think_time))
    computer.set_service(users, Exp.fit_mean(1.0 / base_rate))
    computer.set_load_dependence(
        np.array(
            [
                central[min(n, MEMORY_LIMIT)]["throughput"] / base_rate
                for n in range(1, terminals + 1)
            ],
            dtype=float,
        )
    )
    model.link(Network.serialRouting(terminal, computer))
    return model


def birth_death_result(terminals, think_time, central, memory_limit):
    service_rates = [
        central[min(n, memory_limit)]["throughput"]
        for n in range(terminals + 1)
    ]
    probs = [1.0]
    for n in range(1, terminals + 1):
        birth_rate = (terminals - (n - 1)) / think_time
        death_rate = service_rates[n]
        probs.append(probs[-1] * birth_rate / death_rate)

    total = sum(probs)
    probs = [p / total for p in probs]

    throughput = sum(probs[n] * service_rates[n] for n in range(1, terminals + 1))
    submitted_jobs = sum(n * probs[n] for n in range(terminals + 1))
    memory_queue_jobs = sum(max(n - memory_limit, 0) * probs[n] for n in range(terminals + 1))
    computer_jobs = sum(min(n, memory_limit) * probs[n] for n in range(terminals + 1))
    response = submitted_jobs / throughput
    memory_queue_response = memory_queue_jobs / throughput
    computer_response = computer_jobs / throughput

    util = {
        station: sum(
            probs[n] * central[min(n, memory_limit)]["util"][station]
            for n in range(1, terminals + 1)
        )
        for station in BASE_DEMANDS
    }

    return {
        "terminals": terminals,
        "throughput": throughput,
        "response": response,
        "computer_response": computer_response,
        "memory_queue_response": memory_queue_response,
        "submitted_jobs": submitted_jobs,
        "computer_jobs": computer_jobs,
        "memory_queue_jobs": memory_queue_jobs,
        "util": util,
        "probs": probs,
    }


def scenario_result(terminals, think_time, demands, memory_limit=MEMORY_LIMIT):
    central = central_results(demands, memory_limit)
    result = birth_death_result(terminals, think_time, central, memory_limit)
    return result, central


def find_mmax(think_time, demands, memory_limit=MEMORY_LIMIT, response_limit=RESPONSE_LIMIT):
    central = central_results(demands, memory_limit)
    last_ok = None
    results = []
    for terminals in range(1, 1000):
        result = birth_death_result(terminals, think_time, central, memory_limit)
        results.append(result)
        if result["response"] <= response_limit:
            last_ok = result
        elif last_ok is not None:
            return last_ok, results, central
    raise RuntimeError("Search limit reached before response exceeded the target.")


def scaled_demands(cpu_factor=1.0, disk1_factor=1.0, disk2_factor=1.0):
    return {
        "CPU": BASE_DEMANDS["CPU"] / cpu_factor,
        "Disk1": BASE_DEMANDS["Disk1"] / disk1_factor,
        "Disk2": BASE_DEMANDS["Disk2"] / disk2_factor,
    }


def minimum_factor_for_target(station, terminals, think_time):
    lo = 1.0
    hi = 2.0
    max_hi = 64.0

    def response_for(factor):
        factors = {"CPU": 1.0, "Disk1": 1.0, "Disk2": 1.0}
        factors[station] = factor
        result, _ = scenario_result(
            terminals,
            think_time,
            scaled_demands(
                cpu_factor=factors["CPU"],
                disk1_factor=factors["Disk1"],
                disk2_factor=factors["Disk2"],
            ),
        )
        return result["response"], result

    response, _ = response_for(hi)
    while response > RESPONSE_LIMIT:
        hi *= 2.0
        if hi > max_hi:
            return None, None
        response, _ = response_for(hi)

    best = None
    for _ in range(30):
        mid = (lo + hi) / 2.0
        response, result = response_for(mid)
        if response <= RESPONSE_LIMIT:
            hi = mid
            best = result
        else:
            lo = mid
    return hi, best


def plot_curve(results, mmax):
    x_values = [result["terminals"] for result in results]
    y_values = [result["response"] for result in results]

    plt.figure(figsize=(9, 5))
    plt.plot(x_values, y_values, marker="o", markersize=3, color="#1f6f8b")
    plt.axhline(RESPONSE_LIMIT, color="#b23b3b", linestyle="--", label="3 sec")
    plt.axvline(mmax, color="#4a7c32", linestyle=":", label=f"Mmax = {mmax}")
    plt.xlabel("Number of terminals")
    plt.ylabel("Average transaction response time (sec)")
    plt.title("Questao 7.2 - response time versus terminals")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig("7_2_response_vs_terminals.png", dpi=160)


def main():
    mmax_result, curve_results, central = find_mmax(NEW_THINK_TIME, BASE_DEMANDS)
    mmax = mmax_result["terminals"]
    target_terminals = int(np.ceil(1.2 * mmax))

    plot_limit = max(target_terminals + 10, mmax + 20)
    plotted_results = [
        birth_death_result(m, NEW_THINK_TIME, central, MEMORY_LIMIT)
        for m in range(1, plot_limit + 1)
    ]
    plot_curve(plotted_results, mmax)

    target_base, _ = scenario_result(target_terminals, NEW_THINK_TIME, BASE_DEMANDS)
    upgrade_options = {}
    for station in ["CPU", "Disk1", "Disk2"]:
        factor, result = minimum_factor_for_target(station, target_terminals, NEW_THINK_TIME)
        upgrade_options[station] = {"factor": factor, "result": result}
    viable_options = {
        station: option
        for station, option in upgrade_options.items()
        if option["factor"] is not None
    }
    recommendation = min(viable_options.items(), key=lambda item: item[1]["factor"])

    print("Dados derivados da Table 7.7")
    print(f"Throughput observado: {BASE_THROUGHPUT:.6f} transacoes/s")
    print(f"Tempo de pensar original: {BASE_THINK_TIME:.6f} s")
    print(f"Novo tempo de pensar: {NEW_THINK_TIME:.6f} s")
    print("Demandas de servico")
    for station, demand in BASE_DEMANDS.items():
        print(f"{station}: {demand:.6f} s")

    print("\nTaxas do subsistema CPU/discos por MVA do LINE Solver")
    print("N_ativo  Throughput  RespT")
    for n in range(1, MEMORY_LIMIT + 1):
        print(f"{n:<8} {central[n]['throughput']:.6f}    {central[n]['response']:.6f}")

    print("\nResultado do novo cenario")
    print(f"Mmax: {mmax}")
    print(f"Response time at Mmax: {mmax_result['response']:.6f} s")
    print(f"Throughput at Mmax: {mmax_result['throughput']:.6f} transacoes/s")
    print(f"Computer-system response at Mmax: {mmax_result['computer_response']:.6f} s")
    print(f"Memory-queue response at Mmax: {mmax_result['memory_queue_response']:.6f} s")
    print("Utilizacoes em Mmax")
    for station, util in mmax_result["util"].items():
        print(f"{station}: {util:.6f}")

    print("\nCurva resposta versus terminais")
    print("Terminals  RespT")
    for result in plotted_results:
        print(f"{result['terminals']:<9} {result['response']:.6f}")
    print("Graph saved to 7_2_response_vs_terminals.png")

    print("\nAnalise para 1.2 x Mmax")
    print(f"Target terminals: {target_terminals}")
    print(f"Base response at target: {target_base['response']:.6f} s")
    print("Single-device upgrade factors required for R <= 3 sec")
    for station, option in upgrade_options.items():
        result = option["result"]
        if result is None:
            print(f"{station}: not enough as a single-device upgrade up to factor 64")
        else:
            print(
                f"{station}: factor={option['factor']:.6f}, "
                f"response={result['response']:.6f}, "
                f"CPU_util={result['util']['CPU']:.6f}, "
                f"Disk1_util={result['util']['Disk1']:.6f}, "
                f"Disk2_util={result['util']['Disk2']:.6f}"
            )
    print(
        f"Recommended single-device upgrade: {recommendation[0]} "
        f"by factor {recommendation[1]['factor']:.6f}"
    )


if __name__ == "__main__":
    main()




""" o modelo obteve throughput observado de 3,28 transações/s, tempo de pensar original de 30,02 s e novo tempo
  de pensar de 18,01 s; com a limitação de memória de 5 transações simultâneas, o maior número de terminais
  antes de o tempo de resposta ultrapassar 3 s é Mmax = 141, com resposta média de 2,958 s. Nesse ponto,
  apenas 0,727 s são gastos no subsistema computacional CPU/discos e 2,231 s são gastos esperando memória,
  mostrando que a contenção de memória domina a resposta. As utilizações em Mmax são CPU = 53,30%, Disk1 =
  84,06% e Disk2 = 67,65%, indicando o Disk1 como principal recurso físico carregado. Para suportar 1,2 x
  Mmax = 170 terminais mantendo resposta média de 3 s, o cenário original ficaria em 6,977 s; a recomendação
  do modelo é acelerar o Disk1 em aproximadamente 1,571x, pois upgrades isolados na CPU ou no Disk2 não
  atingem a meta mesmo com fatores altos, enquanto esse upgrade reduz a resposta para 3 s com utilizações
  balanceadas entre CPU = 64,14%, Disk1 = 64,38% e Disk2 = 81,40%."""