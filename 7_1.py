"""
Questão 7.1

Enunciado:
Consider the CS model discussed in the telemarketing company problem and
assume that the server will be upgraded by a two-processor server where each
processor is identical to the original processor. If the same disk is used, solve
the CS model assuming that the service rate, (/), for the server CPU is such
that w(2) = 1.8u(1).
"""

import numpy as np
from line_solver import *


# Parameters from docs/csProblem, Table 7.1.
N_SQL_PER_CALL = 4
D_CLIENT_PER_CALL = 45.0
D_SERVER_CPU = 0.12
D_SERVER_DISK = 0.054
BANDWIDTH_BPS = 10_000_000
SLOT_DURATION = 51.2e-6
AVG_PACKET_LENGTH_BITS = 1518
PACKETS_PER_SQL = 7

# The text concludes that the original telemarketing system needs
# 175 representatives/workstations to meet the call waiting-time target.
WORKSTATIONS = 175


def ethernet_packet_rate(stations):
    if stations <= 1:
        avg_collisions = 0.0
    else:
        success_prob = (1.0 - 1.0 / stations) ** (stations - 1)
        avg_collisions = (1.0 - success_prob) / success_prob
    return 1.0 / (AVG_PACKET_LENGTH_BITS / BANDWIDTH_BPS + SLOT_DURATION * avg_collisions)


def network_sql_rate(contending_workstations):
    if contending_workstations == 1:
        packet_rate = ethernet_packet_rate(1)
    else:
        packet_rate = ethernet_packet_rate(contending_workstations + 1)
    return packet_rate / PACKETS_PER_SQL


def build_cs_model(population, upgraded_cpu):
    model = Network("Questao_7_1_CS_model")
    client = Delay(model, "Client delay")
    network = Queue(model, "Network", SchedStrategy.FCFS)
    server_cpu = Queue(model, "Server CPU", SchedStrategy.FCFS)
    server_disk = Queue(model, "Server disk", SchedStrategy.FCFS)
    users = ClosedClass(model, "SQL requests", population, client)

    client.set_service(users, Exp.fit_mean(D_CLIENT_PER_CALL / N_SQL_PER_CALL))
    network.set_service(users, Exp.fit_mean(1.0 / network_sql_rate(1)))
    server_cpu.set_service(users, Exp.fit_mean(D_SERVER_CPU))
    server_disk.set_service(users, Exp.fit_mean(D_SERVER_DISK))

    network.set_load_dependence(
        np.array(
            [network_sql_rate(j) / network_sql_rate(1) for j in range(1, population + 1)],
            dtype=float,
        )
    )

    if upgraded_cpu:
        server_cpu.set_load_dependence(
            np.array([1.0] + [1.8] * (population - 1), dtype=float)
        )

    model.link(Network.serialRouting(client, network, server_cpu, server_disk))
    return model


def solve_with_line(population, upgraded_cpu):
    model = build_cs_model(population, upgraded_cpu)
    solver = SolverMVA(model)
    return solver.get_avg_table()


def station_value(table, station, column):
    return float(table.data.loc[table.data["Station"] == station, column].iloc[0])


def print_scenario(label, table):
    sql_tput = station_value(table, "Server CPU", "Tput")
    call_tput = sql_tput / N_SQL_PER_CALL
    total_response = sum(float(value) for value in table.data["RespT"])
    system_response = total_response - D_CLIENT_PER_CALL / N_SQL_PER_CALL

    print(label)
    print(table)
    print(f"SQL throughput: {sql_tput:.6f} SQL requests/sec")
    print(f"Call throughput: {call_tput:.6f} calls/sec")
    print(f"SQL cycle response time: {total_response:.6f} sec/request")
    print(f"CS system response time, excluding client delay: {system_response:.6f} sec/request")
    print()

    return {
        "sql_tput": sql_tput,
        "call_tput": call_tput,
        "system_response": system_response,
        "cpu_util": station_value(table, "Server CPU", "Util"),
        "disk_util": station_value(table, "Server disk", "Util"),
        "cpu_qlen": station_value(table, "Server CPU", "QLen"),
        "disk_qlen": station_value(table, "Server disk", "QLen"),
    }


def main():
    original_table = solve_with_line(WORKSTATIONS, upgraded_cpu=False)
    upgraded_table = solve_with_line(WORKSTATIONS, upgraded_cpu=True)

    print(f"Questao 7.1 - LINE Solver MVA, m={WORKSTATIONS} client workstations\n")
    original = print_scenario("Original one-CPU server", original_table)
    upgraded = print_scenario(
        "Upgraded two-processor server, alpha_cpu(1)=1.0 and alpha_cpu(n>=2)=1.8",
        upgraded_table,
    )

    improvement = (upgraded["sql_tput"] / original["sql_tput"] - 1.0) * 100.0
    print("Comparison")
    print(f"Throughput improvement: {improvement:.2f}%")
    print(f"CPU utilization: {original['cpu_util']:.6f} -> {upgraded['cpu_util']:.6f}")
    print(f"Disk utilization: {original['disk_util']:.6f} -> {upgraded['disk_util']:.6f}")
    print(f"CPU queue length: {original['cpu_qlen']:.6f} -> {upgraded['cpu_qlen']:.6f}")
    print(f"Disk queue length: {original['disk_qlen']:.6f} -> {upgraded['disk_qlen']:.6f}")


if __name__ == "__main__":
    main()


""" A saída mostra que, com m=175, o servidor original tem throughput de 8.278502 SQL/s, ou 2.069626
  chamadas/s, com CPU quase saturada (Util=0.993420) e fila média alta na CPU (QLen=81.053201); com o servidor de dois processadores modelado
  por alpha_cpu(1)=1.0 e alpha_cpu(n>=2)=1.8, o throughput sobe para 14.057449 SQL/s, ou 3.514362 chamadas/s, representando melhoria de 69.81%.
  A fila média da CPU cai para 13.743012, enquanto a utilização do disco sobe de 0.447039 para 0.759102, indicando que o upgrade remove grande
  parte do gargalo da CPU e desloca mais carga para o disco."""