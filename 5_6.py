"""
Questao 5.6

Enunciado:
Referring to the motivating example in Sec. 5.3, by how much is CPU throughput improved if 10% of the files are moved from the slow disk to the fast disk?
What about 50%? (This implies changing the value of p.)
"""

from line_solver import *


def build_model(name, p_fast):
    model = Network(name)

    cpu = Queue(model, "CPU", SchedStrategy.FCFS)
    fast = Queue(model, "FastDisk", SchedStrategy.FCFS)
    slow = Queue(model, "SlowDisk", SchedStrategy.FCFS)

    users = ClosedClass(model, "Users", 2, cpu)

    cpu.set_service(users, Exp.fit_mean(10.0))
    fast.set_service(users, Exp.fit_mean(20.0))
    slow.set_service(users, Exp.fit_mean(30.0))

    P = model.init_routing_matrix()
    P.set(users, users, cpu, fast, p_fast)
    P.set(users, users, cpu, slow, 1.0 - p_fast)
    P.set(users, users, fast, cpu, 1.0)
    P.set(users, users, slow, cpu, 1.0)

    model.link(P)
    return model


def solve(name, p_fast):
    model = build_model(name, p_fast)
    solver = SolverMVA(model)
    table = solver.get_avg_table()
    print(f"\n{name} (p_fast = {p_fast:.2f})")
    print(table)
    return table


def as_float(table, station, metric):
    value = table.data.loc[table.data["Station"] == station, metric].iloc[0]
    return float(value)


def total_residence_time(table):
    return table.data["ResidT"].astype(float).sum()


def compare(label, original_table, scenario_table):
    original_cpu_tput = as_float(original_table, "CPU", "Tput")
    scenario_cpu_tput = as_float(scenario_table, "CPU", "Tput")
    original_resid = total_residence_time(original_table)
    scenario_resid = total_residence_time(scenario_table)
    tput_gain = (scenario_cpu_tput / original_cpu_tput - 1.0) * 100.0
    resid_reduction = (1.0 - scenario_resid / original_resid) * 100.0

    print(f"\nComparacao: {label}")
    print(f"Throughput da CPU original: {original_cpu_tput:.6f} transacoes/s")
    print(f"Throughput da CPU no cenario: {scenario_cpu_tput:.6f} transacoes/s")
    print(f"Melhoria de throughput da CPU: {tput_gain:.2f}%")
    print(f"Tempo de residencia total original: {original_resid:.6f} s")
    print(f"Tempo de residencia total no cenario: {scenario_resid:.6f} s")
    print(f"Reducao do tempo de residencia total: {resid_reduction:.2f}%")


original = solve("Sistema original", 0.50)
move_10 = solve("10% dos arquivos movidos do disco lento para o rapido", 0.60)
move_50 = solve("50% dos arquivos movidos do disco lento para o rapido", 1.00)

compare("10% movidos", original, move_10)
compare("50% movidos", original, move_50)

"""Assumindo p como a probabilidade de acessar o disco rápido, o sistema original usa p = 0,50; ao mover 10%
  dos arquivos do disco lento para o rápido, p = 0,60, e o throughput da CPU sobe de 0,042424 para 0,044041 transações/s, uma melhora de 3,81%,
  com redução do tempo de residência total de 47,14 s para 45,41 s. Ao mover 50%, p = 1,00, o throughput da CPU fica em 0,042857 transações/s,
  melhora de apenas 1,02%, pois todo o acesso a disco passa a se concentrar no disco rápido, que se torna o gargalo com utilização de 85,71% e
  fila média de 1,4286; portanto, mover uma parte moderada dos arquivos melhora o balanceamento entre os discos, mas mover todos os arquivos
  para o disco rápido piora o equilíbrio do sistema."""