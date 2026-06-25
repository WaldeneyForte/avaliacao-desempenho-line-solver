"""
Questao 5.17

Enunciado:
Perform simple bounding analysis using ABA and BJB on the example shown in
docs/FIG_5.6.png Graph the ABA bounds, the BJB bounds, and the actual performance
curves. Show all work.
"""

from line_solver import *
from line_solver.api.pfqn.bounds import pfqn_xzabaup

import contextlib
import io
import os

os.environ["MPLCONFIGDIR"] = os.path.join(os.getcwd(), ".matplotlib_cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

import matplotlib.pyplot as plt


CPU_RATE = 10.0
FAST_DISK_RATE = 8.0
SLOW_DISK_RATE = 6.0
P_FAST = 0.7
P_SLOW = 1.0 - P_FAST
MAX_POPULATION = 30

CPU_DEMAND = 1.0 / CPU_RATE
FAST_DISK_DEMAND = P_FAST / FAST_DISK_RATE
SLOW_DISK_DEMAND = P_SLOW / SLOW_DISK_RATE
DEMANDS = [CPU_DEMAND, FAST_DISK_DEMAND, SLOW_DISK_DEMAND]
TOTAL_DEMAND = sum(DEMANDS)
BOTTLENECK_DEMAND = max(DEMANDS)


def build_model(population):
    model = Network(f"FIG 5.6 N={population}")

    cpu = Queue(model, "CPU", SchedStrategy.FCFS)
    fast_disk = Queue(model, "FastDisk", SchedStrategy.FCFS)
    slow_disk = Queue(model, "SlowDisk", SchedStrategy.FCFS)

    jobs = ClosedClass(model, "Jobs", population, cpu)

    cpu.set_service(jobs, Exp.fit_mean(1.0 / CPU_RATE))
    fast_disk.set_service(jobs, Exp.fit_mean(1.0 / FAST_DISK_RATE))
    slow_disk.set_service(jobs, Exp.fit_mean(1.0 / SLOW_DISK_RATE))

    P = model.init_routing_matrix()
    P.set(jobs, jobs, cpu, fast_disk, P_FAST)
    P.set(jobs, jobs, cpu, slow_disk, P_SLOW)
    P.set(jobs, jobs, fast_disk, cpu, 1.0)
    P.set(jobs, jobs, slow_disk, cpu, 1.0)

    model.link(P)
    return model


def solver_throughput(population, method):
    options = SolverOptions()
    options.method = method
    solver = SolverMVA(build_model(population), options)
    with contextlib.redirect_stdout(io.StringIO()):
        table = solver.get_avg_table()
    return float(table.data.loc[table.data["Station"] == "CPU", "Tput"].iloc[0])


def aba_lower_throughput(population):
    # The installed SolverMVA ABA wrapper fails for this model; keep the
    # textbook lower-bound formula to preserve the expected curve.
    response_upper = TOTAL_DEMAND + (population - 1) * BOTTLENECK_DEMAND
    return population / response_upper


def aba_upper_throughput(population):
    return pfqn_xzabaup(DEMANDS, population, 0.0)


populations = list(range(1, MAX_POPULATION + 1))
actual = []
bjb_lower = []
bjb_upper = []
aba_lower = []
aba_upper = []

for population in populations:
    actual.append(solver_throughput(population, "exact"))
    bjb_lower.append(solver_throughput(population, "bjb.lower"))
    bjb_upper.append(solver_throughput(population, "bjb.upper"))
    aba_lower.append(aba_lower_throughput(population))
    aba_upper.append(aba_upper_throughput(population))

print("Work")
print(f"Service rates: mu_CPU={CPU_RATE:.6f}, mu_fast={FAST_DISK_RATE:.6f}, mu_slow={SLOW_DISK_RATE:.6f}")
print(f"Routing probabilities: p_fast={P_FAST:.6f}, p_slow={P_SLOW:.6f}")
print(f"Demand CPU: 1/mu_CPU = {CPU_DEMAND:.6f}")
print(f"Demand FastDisk: p_fast/mu_fast = {FAST_DISK_DEMAND:.6f}")
print(f"Demand SlowDisk: p_slow/mu_slow = {SLOW_DISK_DEMAND:.6f}")
print(f"Total demand D = {TOTAL_DEMAND:.6f}")
print(f"Bottleneck demand Dmax = {BOTTLENECK_DEMAND:.6f}")
print("ABA formulas:")
print("X_lower(N) = N / (D + (N - 1) * Dmax)")
print("X_upper(N) = min(N / D, 1 / Dmax)")

print("\nCurves")
print("N  ABA_lower  Actual  ABA_upper  BJB_lower  BJB_upper")
for i, population in enumerate(populations):
    print(
        f"{population:2d}  "
        f"{aba_lower[i]:.6f}   "
        f"{actual[i]:.6f}  "
        f"{aba_upper[i]:.6f}   "
        f"{bjb_lower[i]:.6f}    "
        f"{bjb_upper[i]:.6f}"
    )

plt.figure(figsize=(10, 6))
plt.plot(populations, aba_lower, label="ABA lower", linestyle="--", color="#9c3b2f")
plt.plot(populations, aba_upper, label="ABA upper", linestyle="--", color="#9c3b2f")
plt.plot(populations, bjb_lower, label="BJB lower", linestyle=":", color="#245a8d")
plt.plot(populations, bjb_upper, label="BJB upper", linestyle=":", color="#245a8d")
plt.plot(populations, actual, label="Actual MVA", linewidth=2.0, color="#1f7a3a")
plt.xlabel("Multiprogramming level N")
plt.ylabel("System throughput")
plt.title("FIG 5.6 Throughput Bounds and Actual Performance")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("5_17_bounds.png", dpi=160)

figure_n = 3
index = figure_n - 1
print("\nFIG 5.6 point, N = 3")
print(f"ABA lower throughput: {aba_lower[index]:.6f}")
print(f"Actual throughput: {actual[index]:.6f}")
print(f"ABA upper throughput: {aba_upper[index]:.6f}")
print(f"BJB lower throughput: {bjb_lower[index]:.6f}")
print(f"BJB upper throughput: {bjb_upper[index]:.6f}")
print("\nGraph saved to 5_17_bounds.png")


"""A análise da Figura 5.6 usa os parâmetros μ_CPU = 10, μ_fast = 8, μ_slow = 6, com probabilidade p = 0,7 de acesso ao disco rápido e 0,3 ao disco lento. As demandas médias por job são D_CPU = 0,100000, D_fast = 0,087500 e D_slow = 0,050000, resultando em demanda total D = 0,237500 e gargalo na CPU, pois Dmax = 0,100000. Para N = 3, o throughput real obtido por MVA é 7,327103 jobs por unidade de tempo, enquanto os limites ABA são 6,857143 como limite inferior e 10,000000 como limite superior. As curvas mostram que, à medida que o nível de multiprogramação aumenta, o throughput cresce e se aproxima do limite assintótico de 10, imposto pelo gargalo da CPU. No gráfico, as curvas BJB ficaram sobrepostas à curva real, indicando que, para este exemplo, esses limites são bastante apertados."""
