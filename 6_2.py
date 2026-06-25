"""
Questao 6.2

Enunciado:
In the example of the transaction system of Sec. 6.2 it is noted that query
transactions only make use of disk 1, which increases its utilization and turns it
into the bottleneck. Having observed this problem, the support analyst wants
to know what would be the effect on performance if the I/O load due to query
transactions were balanced among the two disks. Compare the results obtained
with the current situation.
"""

from line_solver import *

import contextlib
import io


POPULATION = {"Query": 3, "Update": 1}

CURRENT_DEMANDS = {
    "CPU": {"Query": 0.105, "Update": 0.375},
    "Disk1": {"Query": 0.180, "Update": 0.480},
    "Disk2": {"Query": 0.000, "Update": 0.240},
}

BALANCED_DEMANDS = {
    "CPU": {"Query": 0.105, "Update": 0.375},
    "Disk1": {"Query": 0.090, "Update": 0.480},
    "Disk2": {"Query": 0.090, "Update": 0.240},
}


def build_model(name, demands):
    model = Network(name)

    cpu = Queue(model, "CPU", SchedStrategy.PS)
    disk1 = Queue(model, "Disk1", SchedStrategy.PS)
    disk2 = Queue(model, "Disk2", SchedStrategy.PS)

    query = ClosedClass(model, "Query", POPULATION["Query"], cpu)
    update = ClosedClass(model, "Update", POPULATION["Update"], cpu)

    cpu.set_service(query, Exp.fit_mean(demands["CPU"]["Query"]))
    disk1.set_service(query, Exp.fit_mean(demands["Disk1"]["Query"]))
    if demands["Disk2"]["Query"] > 0:
        disk2.set_service(query, Exp.fit_mean(demands["Disk2"]["Query"]))
    cpu.set_service(update, Exp.fit_mean(demands["CPU"]["Update"]))
    disk1.set_service(update, Exp.fit_mean(demands["Disk1"]["Update"]))
    disk2.set_service(update, Exp.fit_mean(demands["Disk2"]["Update"]))

    P = model.init_routing_matrix()
    P.set(query, query, cpu, disk1, 1.0)
    if demands["Disk2"]["Query"] > 0:
        P.set(query, query, disk1, disk2, 1.0)
        P.set(query, query, disk2, cpu, 1.0)
    else:
        P.set(query, query, disk1, cpu, 1.0)
    P.set(update, update, cpu, disk1, 1.0)
    P.set(update, update, disk1, disk2, 1.0)
    P.set(update, update, disk2, cpu, 1.0)

    model.link(P)
    return model


def solve(name, demands):
    options = SolverOptions()
    options.method = "exact"
    solver = SolverMVA(build_model(name, demands), options)
    with contextlib.redirect_stdout(io.StringIO()):
        table = solver.get_avg_table()
    print(f"\n{name}")
    print(table)
    return table


def metric(table, station, job_class, column):
    values = table.data.loc[
        (table.data["Station"] == station) & (table.data["JobClass"] == job_class),
        column,
    ]
    if values.empty:
        return 0.0
    return float(values.iloc[0])


def class_summary(table, job_class):
    rows = table.data.loc[table.data["JobClass"] == job_class]
    return {
        "tput": float(rows["Tput"].astype(float).max()),
        "resp": float(rows["ResidT"].astype(float).sum()),
        "qlen": float(rows["QLen"].astype(float).sum()),
    }


def station_util(table, station):
    rows = table.data.loc[table.data["Station"] == station]
    return float(rows["Util"].astype(float).sum())


current = solve("Situacao atual", CURRENT_DEMANDS)
balanced = solve("I/O de Query balanceado entre Disk1 e Disk2", BALANCED_DEMANDS)

current_query = class_summary(current, "Query")
current_update = class_summary(current, "Update")
balanced_query = class_summary(balanced, "Query")
balanced_update = class_summary(balanced, "Update")

query_tput_gain = (balanced_query["tput"] / current_query["tput"] - 1.0) * 100.0
query_resp_reduction = (1.0 - balanced_query["resp"] / current_query["resp"]) * 100.0
update_tput_gain = (balanced_update["tput"] / current_update["tput"] - 1.0) * 100.0
update_resp_reduction = (1.0 - balanced_update["resp"] / current_update["resp"]) * 100.0

print("\nComparacao por classe")
print("Classe  Tput_atual  Tput_balanceado  Resp_atual  Resp_balanceado")
print(
    f"Query   {current_query['tput']:.6f}    {balanced_query['tput']:.6f}        "
    f"{current_query['resp']:.6f}    {balanced_query['resp']:.6f}"
)
print(
    f"Update  {current_update['tput']:.6f}    {balanced_update['tput']:.6f}        "
    f"{current_update['resp']:.6f}    {balanced_update['resp']:.6f}"
)

print("\nUtilizacao agregada por dispositivo")
print("Dispositivo  Atual     Balanceado")
for station in ["CPU", "Disk1", "Disk2"]:
    print(f"{station:<11} {station_util(current, station):.6f}  {station_util(balanced, station):.6f}")

print("\nGanhos")
print(f"Melhoria do throughput de Query: {query_tput_gain:.2f}%")
print(f"Reducao do tempo de resposta de Query: {query_resp_reduction:.2f}%")
print(f"Melhoria do throughput de Update: {update_tput_gain:.2f}%")
print(f"Reducao do tempo de resposta de Update: {update_resp_reduction:.2f}%")


"""A saída mostra que o throughput das queries aumenta de 4,093886 para 5,246529 transações/s, uma melhora de 28,16%, enquanto o tempo de
  resposta das queries cai de 0,732800 s para 0,571807 s, redução de 21,97%. Para updates, o throughput também melhora, de 0,409333 para
  0,456119 transações/s, e o tempo de resposta cai de 2,443000 s para 2,192411 s. A utilização do Disk1, que era o gargalo com 93,34%, cai para
  69,11%, enquanto o Disk2 sobe para 58,17%, indicando que o balanceamento reduz o gargalo no disco 1 e distribui melhor a carga do sistema."""