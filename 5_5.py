"""
Questão 5.5

Enunciado:
Referring to the motivating example in Sec. 5.3, by how much would performance
be improved if the slow disk were replaced by a second fast disk
"""

from line_solver import *


def build_model(name, slow_disk_service_time):
    model = Network(name)

    cpu = Queue(model, "CPU", SchedStrategy.FCFS)
    fast = Queue(model, "FastDisk", SchedStrategy.FCFS)
    slow = Queue(model, "SlowDisk", SchedStrategy.FCFS)

    users = ClosedClass(model, "Users", 2, cpu)

    cpu.set_service(users, Exp.fit_mean(10.0))
    fast.set_service(users, Exp.fit_mean(20.0))
    slow.set_service(users, Exp.fit_mean(slow_disk_service_time))

    P = model.init_routing_matrix()
    P.set(users, users, cpu, fast, 0.5)
    P.set(users, users, cpu, slow, 0.5)
    P.set(users, users, fast, cpu, 1.0)
    P.set(users, users, slow, cpu, 1.0)

    model.link(P)
    return model


def solve(name, slow_disk_service_time):
    model = build_model(name, slow_disk_service_time)
    solver = SolverMVA(model)
    table = solver.get_avg_table()
    print(f"\n{name}")
    print(table)
    return table


def as_float(table, station, metric):
    value = table.data.loc[table.data["Station"] == station, metric].iloc[0]
    return float(value)


original = solve("Sistema original", 30.0)
improved = solve("Segundo disco rapido", 20.0)

original_cpu_tput = as_float(original, "CPU", "Tput")
improved_cpu_tput = as_float(improved, "CPU", "Tput")
original_total_resid = original.data["ResidT"].astype(float).sum()
improved_total_resid = improved.data["ResidT"].astype(float).sum()
original_max_util = original.data["Util"].astype(float).max()
improved_max_util = improved.data["Util"].astype(float).max()

tput_gain = (improved_cpu_tput / original_cpu_tput - 1.0) * 100.0
resid_reduction = (1.0 - improved_total_resid / original_total_resid) * 100.0
max_util_reduction = (1.0 - improved_max_util / original_max_util) * 100.0

print("\nComparacao")
print(f"Throughput da CPU original: {original_cpu_tput:.6f} transacoes/s")
print(f"Throughput da CPU melhorado: {improved_cpu_tput:.6f} transacoes/s")
print(f"Melhoria de throughput: {tput_gain:.2f}%")
print(f"Tempo de residencia total original: {original_total_resid:.6f} s")
print(f"Tempo de residencia total melhorado: {improved_total_resid:.6f} s")
print(f"Reducao do tempo de residencia total: {resid_reduction:.2f}%")
print(f"Maior utilizacao original: {original_max_util:.6f}")
print(f"Maior utilizacao melhorada: {improved_max_util:.6f}")
print(f"Reducao da maior utilizacao: {max_util_reduction:.2f}%")

"""A saída mostra que substituir o disco lento por um segundo disco rápido melhora o throughput da CPU de 0,042424 para 0,050000
  transações/s, ou seja, um ganho de aproximadamente 17,86%; o tempo de residência total cai de 47,14 s para 40,00 s, redução de cerca de 15,15%. No sistema
  original, o disco lento era o gargalo, com utilização de 63,64%, fila média de 0,90909 e tempo de resposta de 42,857 s; no cenário melhorado, CPU, FastDisk e
  SlowDisk ficam equilibrados, todos com utilização de 50% e fila média de 0,66667. Como a soma dos tamanhos médios de fila permanece aproximadamente igual a 2,
  os resultados são consistentes com a população fechada do modelo.
"""