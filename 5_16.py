"""
Questao 5.16

Enunciado:
Consider the CPU/fast disk/slow disk example, with Uc. = 6, Uf = 3, Us = 2,
p = 0.5, and MPL = 2. Solve this system using the decomposition/aggregation
technique and compare the answers by solving the same system using convolution.
"""

from line_solver import *


CPU_DEMAND = 6.0
FAST_SERVICE = 3.0
SLOW_SERVICE = 2.0
P_FAST = 0.5
MPL = 2

FAST_DEMAND = P_FAST * FAST_SERVICE
SLOW_DEMAND = (1.0 - P_FAST) * SLOW_SERVICE


def mva_closed_single_class(demands, population):
    q_lengths = [0.0 for _ in demands]
    throughput = 0.0
    response_times = [0.0 for _ in demands]

    for n in range(1, population + 1):
        response_times = [
            demand * (1.0 + q_lengths[i]) for i, demand in enumerate(demands)
        ]
        total_response = sum(response_times)
        throughput = n / total_response
        q_lengths = [throughput * response for response in response_times]

    return throughput, response_times, q_lengths


def disk_fes_rates(max_population):
    rates = {0: 0.0}
    for n in range(1, max_population + 1):
        throughput, _, _ = mva_closed_single_class([FAST_DEMAND, SLOW_DEMAND], n)
        rates[n] = throughput
    return rates


def aggregate_solution():
    fes_rates = disk_fes_rates(MPL)

    def cpu_factor(jobs):
        return 1.0 if jobs == 0 else CPU_DEMAND ** jobs

    def fes_factor(jobs):
        factor = 1.0
        for n in range(1, jobs + 1):
            factor *= 1.0 / fes_rates[n]
        return factor

    states = []
    normalizer = 0.0
    for cpu_jobs in range(MPL + 1):
        disk_jobs = MPL - cpu_jobs
        weight = cpu_factor(cpu_jobs) * fes_factor(disk_jobs)
        states.append((cpu_jobs, disk_jobs, weight))
        normalizer += weight

    probabilities = [
        (cpu_jobs, disk_jobs, weight / normalizer)
        for cpu_jobs, disk_jobs, weight in states
    ]
    cpu_qlen = sum(cpu_jobs * prob for cpu_jobs, _, prob in probabilities)
    disk_qlen = sum(disk_jobs * prob for _, disk_jobs, prob in probabilities)
    cpu_util = sum(prob for cpu_jobs, _, prob in probabilities if cpu_jobs > 0)
    throughput = cpu_util / CPU_DEMAND
    total_response = MPL / throughput
    cpu_response = cpu_qlen / throughput
    disk_response = disk_qlen / throughput

    return {
        "fes_rates": fes_rates,
        "throughput": throughput,
        "cpu_qlen": cpu_qlen,
        "disk_qlen": disk_qlen,
        "cpu_util": cpu_util,
        "total_response": total_response,
        "cpu_response": cpu_response,
        "disk_response": disk_response,
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
    model = build_full_model()
    options = SolverOptions()
    options.method = "ca"
    solver = SolverNC(model, options)
    return solver.get_avg_table()


aggregation = aggregate_solution()
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

print("\nDecomposicao/agregacao")
print(f"Taxa FES com 1 job no agregado de discos: {aggregation['fes_rates'][1]:.6f}")
print(f"Taxa FES com 2 jobs no agregado de discos: {aggregation['fes_rates'][2]:.6f}")
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
