"""
Questao 5.7

Enunciado:
Referring to the motivating example in Sec. 5.3, what is the optimal file placement across the two disks? (This implies varying the value of p, observing the
effect upon performance, and selecting the optimal value of p.)
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


def solve(p_fast):
    model = build_model(f"Database workstation p={p_fast:.2f}", p_fast)
    solver = SolverMVA(model)
    return solver.get_avg_table()


def as_float(table, station, metric):
    values = table.data.loc[table.data["Station"] == station, metric]
    if values.empty:
        return 0.0
    value = values.iloc[0]
    return float(value)


def row_for_p(p_fast):
    table = solve(p_fast)
    return {
        "p_fast": p_fast,
        "table": table,
        "cpu_tput": as_float(table, "CPU", "Tput"),
        "cpu_util": as_float(table, "CPU", "Util"),
        "fast_util": as_float(table, "FastDisk", "Util"),
        "slow_util": as_float(table, "SlowDisk", "Util"),
        "total_resid": table.data["ResidT"].astype(float).sum(),
        "total_qlen": table.data["QLen"].astype(float).sum(),
    }


p_values = [i / 100 for i in range(101)]
results = [row_for_p(p) for p in p_values]
best = max(results, key=lambda row: row["cpu_tput"])
original = next(row for row in results if abs(row["p_fast"] - 0.50) < 1e-9)

print("Variacao de p")
print("p_fast  CPU_Tput  CPU_Util  Fast_Util  Slow_Util  Total_Resid  Total_QLen")
for row in results:
    is_summary_point = int(round(row["p_fast"] * 100)) % 5 == 0
    is_best_point = abs(row["p_fast"] - best["p_fast"]) < 1e-9
    if not (is_summary_point or is_best_point):
        continue
    print(
        f"{row['p_fast']:.2f}    "
        f"{row['cpu_tput']:.6f}  "
        f"{row['cpu_util']:.6f}  "
        f"{row['fast_util']:.6f}   "
        f"{row['slow_util']:.6f}   "
        f"{row['total_resid']:.6f}    "
        f"{row['total_qlen']:.6f}"
    )

gain = (best["cpu_tput"] / original["cpu_tput"] - 1.0) * 100.0
resid_reduction = (1.0 - best["total_resid"] / original["total_resid"]) * 100.0

print("\nMelhor configuracao")
print(f"p_fast otimo: {best['p_fast']:.2f}")
print(f"p_slow otimo: {1.0 - best['p_fast']:.2f}")
print(f"Throughput da CPU original: {original['cpu_tput']:.6f} transacoes/s")
print(f"Throughput da CPU otimo: {best['cpu_tput']:.6f} transacoes/s")
print(f"Melhoria de throughput da CPU: {gain:.2f}%")
print(f"Tempo de residencia total original: {original['total_resid']:.6f} s")
print(f"Tempo de residencia total otimo: {best['total_resid']:.6f} s")
print(f"Reducao do tempo de residencia total: {resid_reduction:.2f}%")

print("\nTabela detalhada para o p otimo")
print(best["table"])


"""com uma varredura de p entre 0,00 e 1,00 em passos de 0,01, considerando p como a probabilidade de acesso ao disco
  rápido. A melhor configuração encontrada foi p = 0,77, isto é, aproximadamente 77% dos arquivos no disco rápido e 23% no disco lento; nessa
  configuração, o throughput da CPU sobe de 0,042424 para 0,045236 transações/s, uma melhora de 6,63%, e o tempo de residência total cai de
  47,14 s para 44,21 s, redução de 6,22%. O resultado mostra que o desempenho melhora ao deslocar mais arquivos para o disco rápido, mas não é
  ótimo colocar tudo nele, pois isso concentra fila e utilização no disco rápido; o melhor ponto é aquele que distribui a carga de forma mais
  equilibrada entre os discos, mantendo a soma dos tamanhos médios de fila igual à população fechada de dois usuários."""