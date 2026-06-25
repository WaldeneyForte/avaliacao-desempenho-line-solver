"""
Questao 5.8

Enunciado:
Referring to the motivating example in Sec. 5.3, by how much is CPU throughput impruved by increasing the mpl from 2 to 3?
"""

from line_solver import *


def build_model(name, mpl):
    model = Network(name)

    cpu = Queue(model, "CPU", SchedStrategy.FCFS)
    fast = Queue(model, "FastDisk", SchedStrategy.FCFS)
    slow = Queue(model, "SlowDisk", SchedStrategy.FCFS)

    users = ClosedClass(model, "Users", mpl, cpu)

    cpu.set_service(users, Exp.fit_mean(10.0))
    fast.set_service(users, Exp.fit_mean(20.0))
    slow.set_service(users, Exp.fit_mean(30.0))

    P = model.init_routing_matrix()
    P.set(users, users, cpu, fast, 0.5)
    P.set(users, users, cpu, slow, 0.5)
    P.set(users, users, fast, cpu, 1.0)
    P.set(users, users, slow, cpu, 1.0)

    model.link(P)
    return model


def solve(name, mpl):
    model = build_model(name, mpl)
    solver = SolverMVA(model)
    table = solver.get_avg_table()
    print(f"\n{name} (MPL = {mpl})")
    print(table)
    return table


def as_float(table, station, metric):
    value = table.data.loc[table.data["Station"] == station, metric].iloc[0]
    return float(value)


def total_residence_time(table):
    return table.data["ResidT"].astype(float).sum()


mpl_2 = solve("Sistema original", 2)
mpl_3 = solve("Sistema com MPL aumentado", 3)

cpu_tput_2 = as_float(mpl_2, "CPU", "Tput")
cpu_tput_3 = as_float(mpl_3, "CPU", "Tput")
resid_2 = total_residence_time(mpl_2)
resid_3 = total_residence_time(mpl_3)
qlen_2 = mpl_2.data["QLen"].astype(float).sum()
qlen_3 = mpl_3.data["QLen"].astype(float).sum()
tput_gain = (cpu_tput_3 / cpu_tput_2 - 1.0) * 100.0
resid_increase = (resid_3 / resid_2 - 1.0) * 100.0

print("\nComparacao")
print(f"Throughput da CPU com MPL 2: {cpu_tput_2:.6f} transacoes/s")
print(f"Throughput da CPU com MPL 3: {cpu_tput_3:.6f} transacoes/s")
print(f"Melhoria de throughput da CPU: {tput_gain:.2f}%")
print(f"Tempo de residencia total com MPL 2: {resid_2:.6f} s")
print(f"Tempo de residencia total com MPL 3: {resid_3:.6f} s")
print(f"Aumento do tempo de residencia total: {resid_increase:.2f}%")
print(f"Soma dos QLen com MPL 2: {qlen_2:.6f}")
print(f"Soma dos QLen com MPL 3: {qlen_3:.6f}")


""" A saída mostra que, ao aumentar o MPL de 2 para 3, o throughput da CPU sobe de 0,042424 para 0,050382 transações/s,
  uma melhora de aproximadamente 18,76%; porém, esse ganho vem acompanhado de maior congestionamento, pois o tempo de residência total aumenta
  de 47,14 s para 59,55 s e o disco lento continua sendo o gargalo, com utilização subindo de 63,64% para 75,57% e fila média de 1,4427. A soma
  dos tamanhos médios de fila passa de 2 para 3, confirmando a consistência do modelo fechado com a nova população."""