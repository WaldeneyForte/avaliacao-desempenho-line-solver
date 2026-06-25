"""
Questao 5.4

Enunciado:
Referring to the motivating example in Sec. 5.3, by how much would performance be improved if code for transaction handling by the CPU were rewritten
to execute 33% faster?
"""

from line_solver import *


def build_model(name, cpu_service_time):
    model = Network(name)

    cpu = Queue(model, "CPU", SchedStrategy.FCFS)
    fast = Queue(model, "FastDisk", SchedStrategy.FCFS)
    slow = Queue(model, "SlowDisk", SchedStrategy.FCFS)

    users = ClosedClass(model, "Users", 2, cpu)

    cpu.set_service(users, Exp.fit_mean(cpu_service_time))
    fast.set_service(users, Exp.fit_mean(20.0))
    slow.set_service(users, Exp.fit_mean(30.0))

    P = model.init_routing_matrix()
    P.set(users, users, cpu, fast, 0.5)
    P.set(users, users, cpu, slow, 0.5)
    P.set(users, users, fast, cpu, 1.0)
    P.set(users, users, slow, cpu, 1.0)

    model.link(P)
    return model


def solve(name, cpu_service_time):
    model = build_model(name, cpu_service_time)
    solver = SolverMVA(model)
    table = solver.get_avg_table()
    print(f"\n{name}")
    print(table)
    return table


def as_float(table, station, metric):
    value = table.data.loc[table.data["Station"] == station, metric].iloc[0]
    return float(value)


original = solve("Sistema original", 10.0)
improved = solve("CPU 33% mais rapida", 10.0 / 1.33)

original_cpu_tput = as_float(original, "CPU", "Tput")
improved_cpu_tput = as_float(improved, "CPU", "Tput")
original_total_resid = original.data["ResidT"].astype(float).sum()
improved_total_resid = improved.data["ResidT"].astype(float).sum()

tput_gain = (improved_cpu_tput / original_cpu_tput - 1.0) * 100.0
resid_reduction = (1.0 - improved_total_resid / original_total_resid) * 100.0

print("\nComparacao")
print(f"Throughput da CPU original: {original_cpu_tput:.6f} transacoes/s")
print(f"Throughput da CPU melhorado: {improved_cpu_tput:.6f} transacoes/s")
print(f"Melhoria de throughput: {tput_gain:.2f}%")
print(f"Tempo de residencia total original: {original_total_resid:.6f} s")
print(f"Tempo de residencia total melhorado: {improved_total_resid:.6f} s")
print(f"Reducao do tempo de residencia total: {resid_reduction:.2f}%")


"""o tempo médio de CPU caiu de 10 s para
  10/1.33 = 7,5188 s. A saída mostra que o throughput da CPU aumentou de 0,042424 para 0,045196 transações/s, uma melhoria de aproximadamente
  6,53%; o tempo de residência total caiu de 47,14 s para 44,25 s, redução de cerca de 6,13%. Apesar da melhora na CPU, o disco lento continua
  sendo o gargalo, com a maior utilização (67,79%), maior fila média (0,99066) e maior tempo de resposta (43,838 s)."""