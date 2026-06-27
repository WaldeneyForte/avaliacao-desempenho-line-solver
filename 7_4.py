"""
Questao 7.4

Enunciado:
The telemarketing company discussed in Sec. 7.2 posed the following problem
to its capacity planner, Alice. Assume that the interaction time between the
telemarketing representative and the customer could be cut down by 40% if
the telemarketing representative had the capability of viewing digitized images
of the products displayed in the catalog instead of having to browse the actual
catalog to answer questions from the customer. This would require buying an
additional disk to store the compressed digitized images. Consider that the
additional service demand at this new disk is equal to 0.3 sec. Consider that
each call requests two images, on the average, to be sent from the server to
the client and that each compressed image is 100 Kbytes long. What is the
minimum number of telemarketing representatives necessary to guarantee that
each customer will not have to wait more than 5 sec on the average before
being served?
"""

from line_solver import *

import contextlib
from functools import lru_cache
from io import StringIO
import math
import warnings

import numpy as np


warnings.filterwarnings("ignore", message=r"\[link\] Reducible network topology detected.*")


CALLS_PER_DAY = 30000
WORKING_HOURS_PER_DAY = 12
ARRIVAL_RATE = CALLS_PER_DAY / (WORKING_HOURS_PER_DAY * 3600)
WAIT_TARGET = 5.0

N_SQL_PER_CALL = 4
BASE_CLIENT_DELAY_PER_SQL = 45.0
NEW_CLIENT_DELAY_PER_SQL = 0.60 * BASE_CLIENT_DELAY_PER_SQL
SERVER_CPU_DEMAND_PER_SQL = 0.12
SERVER_DISK_DEMAND_PER_SQL = 0.054

BANDWIDTH_BPS = 10_000_000
SLOT_DURATION = 51.2e-6
AVG_PACKET_LENGTH_BITS = 1518
MAX_DATA_FIELD_BYTES = 1492
BASE_PACKETS_PER_SQL = 7

IMAGES_PER_CALL = 2
IMAGE_SIZE_BYTES = 100 * 1024
IMAGE_DISK_DEMAND_PER_IMAGE = 0.3
IMAGE_PACKETS_PER_CALL = IMAGES_PER_CALL * math.ceil(
    IMAGE_SIZE_BYTES / MAX_DATA_FIELD_BYTES
)
IMAGE_PACKETS_PER_SQL_EQUIVALENT = IMAGE_PACKETS_PER_CALL / N_SQL_PER_CALL
PACKETS_PER_SQL_EQUIVALENT = BASE_PACKETS_PER_SQL + IMAGE_PACKETS_PER_SQL_EQUIVALENT
IMAGE_DISK_DEMAND_PER_SQL_EQUIVALENT = (
    IMAGES_PER_CALL * IMAGE_DISK_DEMAND_PER_IMAGE / N_SQL_PER_CALL
)


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
    return packet_rate / PACKETS_PER_SQL_EQUIVALENT


def build_cs_model(population):
    model = Network(f"Questao_7_4_CS_model_N_{population}")
    client = Delay(model, "Client interaction")
    network = Queue(model, "Ethernet LAN", SchedStrategy.FCFS)
    server_cpu = Queue(model, "Server CPU", SchedStrategy.FCFS)
    server_disk = Queue(model, "Server disk", SchedStrategy.FCFS)
    image_disk = Queue(model, "Image disk", SchedStrategy.FCFS)
    users = ClosedClass(model, "SQL requests", population, client)

    client.set_service(users, Exp.fit_mean(NEW_CLIENT_DELAY_PER_SQL))
    network.set_service(users, Exp.fit_mean(1.0 / network_sql_rate(1)))
    server_cpu.set_service(users, Exp.fit_mean(SERVER_CPU_DEMAND_PER_SQL))
    server_disk.set_service(users, Exp.fit_mean(SERVER_DISK_DEMAND_PER_SQL))
    image_disk.set_service(users, Exp.fit_mean(IMAGE_DISK_DEMAND_PER_SQL_EQUIVALENT))

    network.set_load_dependence(
        np.array(
            [
                network_sql_rate(j) / network_sql_rate(1)
                for j in range(1, population + 1)
            ],
            dtype=float,
        )
    )

    model.link(Network.serialRouting(client, network, server_cpu, server_disk, image_disk))
    return model


def solve_table(model):
    options = SolverOptions()
    options.method = "default"
    solver = SolverMVA(model, options)
    with contextlib.redirect_stdout(StringIO()):
        return solver.get_avg_table()


def station_value(table, station, column):
    return float(table.data.loc[table.data["Station"] == station, column].iloc[0])


@lru_cache(maxsize=None)
def sql_throughput(workstations):
    table = solve_table(build_cs_model(workstations))
    return station_value(table, "Server CPU", "Tput")


def call_service_rates(representatives):
    rates = [0.0]
    for k in range(1, representatives + 1):
        rates.append(sql_throughput(k) / N_SQL_PER_CALL)
    return rates


def average_waiting_time(representatives):
    mu = call_service_rates(representatives)
    if ARRIVAL_RATE >= mu[representatives]:
        return float("inf"), None

    relative = [1.0]
    for k in range(1, representatives + 1):
        relative.append(relative[-1] * ARRIVAL_RATE / mu[k])

    tail_ratio = ARRIVAL_RATE / mu[representatives]
    tail_mass = relative[representatives] * tail_ratio / (1.0 - tail_ratio)
    p0 = 1.0 / (sum(relative) + tail_mass)
    probabilities = [p0 * value for value in relative]

    avg_waiting_calls = (
        p0
        * relative[representatives]
        * tail_ratio
        / ((1.0 - tail_ratio) ** 2)
    )
    avg_wait = avg_waiting_calls / ARRIVAL_RATE
    return avg_wait, {
        "probabilities": probabilities,
        "avg_waiting_calls": avg_waiting_calls,
        "server_call_rate": mu[representatives],
        "rho_tail": tail_ratio,
    }


def find_minimum_representatives():
    last_wait = None
    for representatives in range(1, 400):
        wait, details = average_waiting_time(representatives)
        if wait <= WAIT_TARGET:
            return representatives, wait, details, last_wait
        last_wait = wait
    raise RuntimeError("Nao foi encontrado numero de representantes ate o limite pesquisado.")


def representative_metrics(representatives):
    table = solve_table(build_cs_model(representatives))
    sql_tput = station_value(table, "Server CPU", "Tput")
    total_sql_response = float(table.data["RespT"].astype(float).sum())
    return {
        "table": table,
        "sql_tput": sql_tput,
        "call_tput": sql_tput / N_SQL_PER_CALL,
        "effective_call_capacity_time": N_SQL_PER_CALL / sql_tput,
        "total_sql_response": total_sql_response,
        "cpu_util": station_value(table, "Server CPU", "Util"),
        "server_disk_util": station_value(table, "Server disk", "Util"),
        "image_disk_util": station_value(table, "Image disk", "Util"),
        "network_util": station_value(table, "Ethernet LAN", "Util"),
    }


def main():
    minimum, wait, details, previous_wait = find_minimum_representatives()
    metrics = representative_metrics(minimum)
    previous_metrics = representative_metrics(minimum - 1)

    print("Parametros derivados da Sec. 7.2 e do enunciado")
    print(f"Arrival rate: {ARRIVAL_RATE:.6f} calls/sec")
    print(f"Client interaction per SQL after 40% reduction: {NEW_CLIENT_DELAY_PER_SQL:.6f} sec")
    print(f"Base packets per SQL: {BASE_PACKETS_PER_SQL}")
    print(f"Image packets per call: {IMAGE_PACKETS_PER_CALL}")
    print(f"Equivalent packets per SQL: {PACKETS_PER_SQL_EQUIVALENT:.6f}")
    print(f"Equivalent image disk demand per SQL: {IMAGE_DISK_DEMAND_PER_SQL_EQUIVALENT:.6f} sec")

    print("\nResultado da busca")
    print(f"Minimum representatives: {minimum}")
    print(f"Average waiting time at {minimum - 1} representatives: {previous_wait:.6f} sec")
    print(f"Average waiting time at {minimum} representatives: {wait:.6f} sec")
    print(f"Call service rate at {minimum} representatives: {details['server_call_rate']:.6f} calls/sec")
    print(f"Tail utilization ratio lambda/mu_m: {details['rho_tail']:.6f}")
    print(f"Average number of waiting calls: {details['avg_waiting_calls']:.6f}")

    print("\nCS model at the minimum")
    print(f"SQL throughput: {metrics['sql_tput']:.6f} SQL/sec")
    print(f"Call throughput capacity: {metrics['call_tput']:.6f} calls/sec")
    print(f"Effective time per call at this population: {metrics['effective_call_capacity_time']:.6f} sec")
    print(f"CPU utilization: {metrics['cpu_util']:.6f}")
    print(f"Server disk utilization: {metrics['server_disk_util']:.6f}")
    print(f"Image disk utilization: {metrics['image_disk_util']:.6f}")
    print(f"Network utilization: {metrics['network_util']:.6f}")
    print("\nLINE Solver average table")
    print(metrics["table"])

    print("\nBorderline comparison")
    print(
        f"{minimum - 1} reps: call capacity={previous_metrics['call_tput']:.6f} calls/sec, "
        f"wait={previous_wait:.6f} sec"
    )
    print(
        f"{minimum} reps: call capacity={metrics['call_tput']:.6f} calls/sec, "
        f"wait={wait:.6f} sec"
    )


if __name__ == "__main__":
    main()

"""A saída mostra que o número mínimo de
  representantes é 84: com 83 representantes o tempo médio de espera ainda fica em 6,01 s, acima do limite,
  enquanto com 84 cai para 4,37 s, satisfazendo a exigência de no máximo 5 s. No cenário com imagens, o tempo
  de interação por SQL cai para 27 s, mas há acréscimo de 138 pacotes por chamada e demanda equivalente de
  0,15 s por SQL no novo disco de imagens; mesmo assim, o recurso mais carregado passa a ser o disco de
  imagens, com utilização de 45,76%, seguido da CPU com 36,61%, enquanto a LAN fica pouco utilizada (1,94%).
  Isso indica que a redução no tempo de interação compensa o custo adicional de imagens e permite operar com
  bem menos representantes do que o caso original da Sec. 7.2, mantendo a espera média dentro da meta."""