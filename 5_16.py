"""
Questao 5.16

Enunciado:
Consider the CPU/fast disk/slow disk example, with Uc. = 6, Uf = 3, Us = 2,
p = 0.5, and MPL = 2. Solve this system using the decomposition/aggregation
technique and compare the answers by solving the same system using convolution.
"""

import contextlib
from io import StringIO

import numpy as np
from line_solver import *


CPU_DEMAND = 6.0
FAST_SERVICE = 3.0
SLOW_SERVICE = 2.0
P_FAST = 0.5
MPL = 2

FAST_DEMAND = P_FAST * FAST_SERVICE
SLOW_DEMAND = (1.0 - P_FAST) * SLOW_SERVICE


def solve_table(model, solver_class, method):
    options = SolverOptions()
    options.method = method
    solver = solver_class(model, options)
    with contextlib.redirect_stdout(StringIO()):
        return solver.get_avg_table()


def build_disk_fes_model(population):
    model = Network(f"Disk FES calibration N={population}")

    fast = Queue(model, "FastDiskDemand", SchedStrategy.FCFS)
    slow = Queue(model, "SlowDiskDemand", SchedStrategy.FCFS)
    jobs = ClosedClass(model, "DiskJobs", population, fast)

    fast.set_service(jobs, Exp.fit_mean(FAST_DEMAND))
    slow.set_service(jobs, Exp.fit_mean(SLOW_DEMAND))
    model.link(Network.serialRouting(fast, slow))
    return model


def disk_fes_rates(max_population):
    rates = {0: 0.0}
    for population in range(1, max_population + 1):
        table = solve_table(build_disk_fes_model(population), SolverMVA, "exact")
        rates[population] = as_float(table, "FastDiskDemand", "Tput")
    return rates


def build_aggregate_model(fes_rates):
    model = Network("CPU plus aggregated disk FES")

    cpu = Queue(model, "CPU", SchedStrategy.FCFS)
    disk_fes = Queue(model, "FES_disks", SchedStrategy.FCFS)
    jobs = ClosedClass(model, "Jobs", MPL, cpu)

    cpu.set_service(jobs, Exp.fit_mean(CPU_DEMAND))
    disk_fes.set_service(jobs, Exp.fit_mean(1.0 / fes_rates[1]))
    disk_fes.set_load_dependence(
        np.array([fes_rates[n] / fes_rates[1] for n in range(1, MPL + 1)])
    )

    model.link(Network.serialRouting(cpu, disk_fes))
    return model


def solve_aggregation():
    fes_rates = disk_fes_rates(MPL)
    table = solve_table(build_aggregate_model(fes_rates), SolverNC, "exact")
    return {
        "fes_rates": fes_rates,
        "table": table,
        "throughput": as_float(table, "CPU", "Tput"),
        "cpu_qlen": as_float(table, "CPU", "QLen"),
        "disk_qlen": as_float(table, "FES_disks", "QLen"),
        "cpu_util": as_float(table, "CPU", "Util"),
        "total_response": table.data["ResidT"].astype(float).sum(),
    }


def build_full_model():
    model = Network("CPU fast disk slow disk")

    cpu = Queue(model, "CPU", SchedStrategy.FCFS)
    fast = Queue(model, "FastDisk", SchedStrategy.FCFS)
    slow = Queue(model, "SlowDisk", SchedStrategy.FCFS)

    jobs = ClosedClass(model, "Jobs", MPL, cpu)

    cpu.set_service(jobs, Exp.fit_mean(CPU_DEMAND))
    fast.set_service(jobs, Exp.fit_mean(FAST_SERVICE))
    slow.set_service(jobs, Exp.fit_mean(SLOW_SERVICE))

    P = model.init_routing_matrix()
    P.set(jobs, jobs, cpu, fast, P_FAST)
    P.set(jobs, jobs, cpu, slow, 1.0 - P_FAST)
    P.set(jobs, jobs, fast, cpu, 1.0)
    P.set(jobs, jobs, slow, cpu, 1.0)

    model.link(P)
    return model


def as_float(table, station, metric):
    value = table.data.loc[table.data["Station"] == station, metric].iloc[0]
    return float(value)


def solve_convolution():
    return solve_table(build_full_model(), SolverNC, "ca")


aggregation = solve_aggregation()
convolution = solve_convolution()

conv_cpu_tput = as_float(convolution, "CPU", "Tput")
conv_total_response = convolution.data["ResidT"].astype(float).sum()
conv_total_qlen = convolution.data["QLen"].astype(float).sum()
conv_disk_qlen = (
    as_float(convolution, "FastDisk", "QLen")
    + as_float(convolution, "SlowDisk", "QLen")
)

print("Parametros")
print(f"D_CPU = {CPU_DEMAND:.6f}")
print(f"D_FastDisk = p * Uf = {FAST_DEMAND:.6f}")
print(f"D_SlowDisk = (1-p) * Us = {SLOW_DEMAND:.6f}")

print("\nDecomposicao/agregacao pelo LINE Solver")
print(f"Taxa FES com 1 job no agregado de discos: {aggregation['fes_rates'][1]:.6f}")
print(f"Taxa FES com 2 jobs no agregado de discos: {aggregation['fes_rates'][2]:.6f}")
print(aggregation["table"])
print(f"Throughput do sistema: {aggregation['throughput']:.6f}")
print(f"Tempo de resposta total: {aggregation['total_response']:.6f}")
print(f"QLen CPU: {aggregation['cpu_qlen']:.6f}")
print(f"QLen agregado dos discos: {aggregation['disk_qlen']:.6f}")
print(f"Utilizacao CPU: {aggregation['cpu_util']:.6f}")

print("\nConvolucao pelo SolverNC")
print(convolution)
print("\nComparacao")
print(f"Throughput agregacao: {aggregation['throughput']:.6f}")
print(f"Throughput convolucao: {conv_cpu_tput:.6f}")
print(f"Diferenca percentual no throughput: {(aggregation['throughput'] / conv_cpu_tput - 1.0) * 100.0:.2f}%")
print(f"Resposta total agregacao: {aggregation['total_response']:.6f}")
print(f"Resposta total convolucao: {conv_total_response:.6f}")
print(f"QLen total convolucao: {conv_total_qlen:.6f}")
print(f"QLen dos discos na convolucao: {conv_disk_qlen:.6f}")
