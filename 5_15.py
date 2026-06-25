"""
Questao 5.15

Enunciado:
A computer system has one CPU and two disks, disk 1 and disk 2. The system
was monitored for 1 hour and the utilization of the CPU and of disk 1 were
measured to be 32% and 60%, respectively. Each transaction makes 5 I/O
requests to disk 1 and 8 to disk 2. The average service time at disk 1 is 30 msec
and at disk 2 is 25 msec.
(a) Find the system throughput.
(b) Find the utilization of disk 2.
(c) Find the average service demands at the CPU, disk 1, and disk 2.
(d) Use MVA to find the system throughput, response time, and average queue
length at the CPU and the disks when the degree of multiprogramming is
N, for N = 0, ..., 4.
(e) Based on your results for item (d), what would be a good approximation for
the average degree of multiprogramming during the measurement interval?
"""

from line_solver import *


CPU_UTIL = 0.32
DISK1_UTIL = 0.60
DISK1_VISITS = 5
DISK2_VISITS = 8
DISK1_SERVICE = 0.030
DISK2_SERVICE = 0.025

DISK1_DEMAND = DISK1_VISITS * DISK1_SERVICE
SYSTEM_THROUGHPUT = DISK1_UTIL / DISK1_DEMAND
CPU_DEMAND = CPU_UTIL / SYSTEM_THROUGHPUT
DISK2_DEMAND = DISK2_VISITS * DISK2_SERVICE
DISK2_UTIL = SYSTEM_THROUGHPUT * DISK2_DEMAND


def build_model(name, mpl):
    model = Network(name)

    cpu = Queue(model, "CPU", SchedStrategy.FCFS)
    disk1 = Queue(model, "Disk1", SchedStrategy.FCFS)
    disk2 = Queue(model, "Disk2", SchedStrategy.FCFS)

    transactions = ClosedClass(model, "Transactions", mpl, cpu)

    cpu.set_service(transactions, Exp.fit_mean(CPU_DEMAND))
    disk1.set_service(transactions, Exp.fit_mean(DISK1_DEMAND))
    disk2.set_service(transactions, Exp.fit_mean(DISK2_DEMAND))

    P = model.init_routing_matrix()
    P.set(transactions, transactions, cpu, disk1, 1.0)
    P.set(transactions, transactions, disk1, disk2, 1.0)
    P.set(transactions, transactions, disk2, cpu, 1.0)

    model.link(P)
    return model


def solve(mpl):
    model = build_model(f"Computer system MPL={mpl}", mpl)
    solver = SolverMVA(model)
    return solver.get_avg_table()


def as_float(table, station, metric):
    value = table.data.loc[table.data["Station"] == station, metric].iloc[0]
    return float(value)


def total_response_time(table):
    return table.data["ResidT"].astype(float).sum()


print("Itens (a), (b) e (c)")
print(f"Throughput do sistema: {SYSTEM_THROUGHPUT:.6f} transacoes/s")
print(f"Utilizacao do disco 2: {DISK2_UTIL:.6f}")
print(f"Demanda media da CPU: {CPU_DEMAND:.6f} s")
print(f"Demanda media do disco 1: {DISK1_DEMAND:.6f} s")
print(f"Demanda media do disco 2: {DISK2_DEMAND:.6f} s")

print("\nItem (d): MVA para MPL 0, 1, 2, 3 e 4")
print("MPL  X_sistema  R_sistema  Q_CPU    Q_Disk1  Q_Disk2")

results = [
    {
        "mpl": 0,
        "table": None,
        "throughput": 0.0,
        "response_time": 0.0,
        "q_cpu": 0.0,
        "q_disk1": 0.0,
        "q_disk2": 0.0,
    }
]
print("0    0.000000   0.000000   0.000000  0.000000  0.000000")

for mpl in range(1, 5):
    table = solve(mpl)
    throughput = as_float(table, "CPU", "Tput")
    response_time = total_response_time(table)
    q_cpu = as_float(table, "CPU", "QLen")
    q_disk1 = as_float(table, "Disk1", "QLen")
    q_disk2 = as_float(table, "Disk2", "QLen")
    results.append(
        {
            "mpl": mpl,
            "table": table,
            "throughput": throughput,
            "response_time": response_time,
            "q_cpu": q_cpu,
            "q_disk1": q_disk1,
            "q_disk2": q_disk2,
        }
    )
    print(
        f"{mpl}    {throughput:.6f}   {response_time:.6f}   "
        f"{q_cpu:.6f}  {q_disk1:.6f}  {q_disk2:.6f}"
    )

closest = min(results, key=lambda row: abs(row["throughput"] - SYSTEM_THROUGHPUT))

print("\nTabela detalhada do MPL mais proximo do throughput medido")
print(closest["table"])
print("\nItem (e)")
print(f"MPL aproximado no intervalo de medicao: {closest['mpl']}")


""" (a) O throughput do sistema é 4,0 transações/s.

  (b) A utilização do disco 2 é 0,80, ou seja, 80%.

  (c) As demandas médias de serviço por transação são: CPU = 0,08 s, disco 1 = 0,15 s e disco 2 = 0,20 s.

  (d) Pela MVA, para N = 0, 1, 2, 3, 4, os resultados são: para N = 0, throughput 0, tempo de resposta 0 e filas médias 0; para N = 1,
  throughput 2,325581 transações/s, resposta 0,430000 s, filas CPU = 0,186047, Disco 1 = 0,348837, Disco 2 = 0,465116; para N = 2, throughput
  3,388495 transações/s, resposta 0,590233 s, filas CPU = 0,321513, Disco 1 = 0,685579, Disco 2 = 0,992908; para N = 3, throughput 3,962282
  transações/s, resposta 0,757139 s, filas CPU = 0,418897, Disco 1 = 1,001811, Disco 2 = 1,579292; para N = 4, throughput 4,302732 transações/
  s, resposta 0,929642 s, filas CPU = 0,488411, Disco 1 = 1,291988, Disco 2 = 2,219601.

  (e) Como o throughput medido no intervalo foi 4,0 transações/s, o valor de MVA mais próximo é o de N = 3, com throughput 3,962282 transações/
  s. Portanto, uma boa aproximação para o grau médio de multiprogramação durante a medição é 3."""