"""
Questao 7.7

Enunciado:
Consider the example given in Sec. 7.7. Assume that the number of workstations
is to be doubled. The proportion of workstations that submit transactions of
each type (trivial, average, and complex) will be kept constant, and so is the
percentage of transactions of each type received by the server. Compute the new
values of the response time and throughput.* What would your recommendation
be to guarantee that the response time for average transactions does not exceed
ZiSECH
"""

from line_solver import *

import contextlib
from io import StringIO
import warnings

import numpy as np


warnings.filterwarnings("ignore", message=r"\[link\] Reducible network topology detected.*")


CLASSES = ["Trivial", "Average", "Complex"]
BASE_POPULATIONS = {"Trivial": 10, "Average": 20, "Complex": 5}
DOUBLED_POPULATIONS = {cls: 2 * population for cls, population in BASE_POPULATIONS.items()}

# Table 7.4, Sec. 7.7.
THINK_TIMES = {"Trivial": 40.0, "Average": 20.0, "Complex": 15.0}
PACKETS_PER_TRANSACTION = {"Trivial": 2, "Average": 3, "Complex": 9}
PACKET_LENGTH_BITS = {"Trivial": 800, "Average": 1382, "Complex": 1410}
CPU_DEMANDS = {"Trivial": 0.030, "Average": 0.255, "Complex": 0.615}
READS_WRITES = {"Trivial": 2, "Average": 17, "Complex": 41}
DISK_SERVICE_TIME = 0.018
DISK_DEMANDS = {
    cls: READS_WRITES[cls] * DISK_SERVICE_TIME
    for cls in CLASSES
}
NETWORK_DEMANDS = {
    "Trivial": 0.00016,
    "Average": 0.00041,
    "Complex": 0.00127,
}

BANDWIDTH_BPS = 10_000_000
SLOT_DURATION = 51.2e-6
AVG_PACKET_LENGTH_BITS = 1286
AVG_PACKETS_PER_TRANSACTION = 3.98
AVERAGE_RESPONSE_TARGET = 2.0


def ethernet_packet_rate(stations):
    if stations <= 1:
        avg_collisions = 0.0
    else:
        success_prob = (1.0 - 1.0 / stations) ** (stations - 1)
        avg_collisions = (1.0 - success_prob) / success_prob
    return 1.0 / (AVG_PACKET_LENGTH_BITS / BANDWIDTH_BPS + SLOT_DURATION * avg_collisions)


def network_transaction_rate(contending_workstations):
    if contending_workstations == 1:
        packet_rate = ethernet_packet_rate(1)
    else:
        packet_rate = ethernet_packet_rate(contending_workstations + 1)
    return packet_rate / AVG_PACKETS_PER_TRANSACTION


def build_model(populations, cpu_factor=1.0, disk_factor=1.0, network_factor=1.0):
    model = Network("Questao_7_7_multiclass_ld_mva")
    client = Delay(model, "Client think time")
    network = Queue(model, "Ethernet LAN", SchedStrategy.FCFS)
    cpu = Queue(model, "Server CPU", SchedStrategy.FCFS)
    disk = Queue(model, "Server disk", SchedStrategy.FCFS)

    class_objects = {}
    for cls in CLASSES:
        class_objects[cls] = ClosedClass(model, cls, populations[cls], client)

    for cls, job_class in class_objects.items():
        client.set_service(job_class, Exp.fit_mean(THINK_TIMES[cls]))
        network.set_service(job_class, Exp.fit_mean(NETWORK_DEMANDS[cls] / network_factor))
        cpu.set_service(job_class, Exp.fit_mean(CPU_DEMANDS[cls] / cpu_factor))
        disk.set_service(job_class, Exp.fit_mean(DISK_DEMANDS[cls] / disk_factor))

    max_population = sum(populations.values())
    network.set_load_dependence(
        np.array(
            [
                network_transaction_rate(n) / network_transaction_rate(1)
                for n in range(1, max_population + 1)
            ],
            dtype=float,
        )
    )

    routing = model.init_routing_matrix()
    for cls, job_class in class_objects.items():
        routing.set(job_class, job_class, client, network, 1.0)
        routing.set(job_class, job_class, network, cpu, 1.0)
        routing.set(job_class, job_class, cpu, disk, 1.0)
        routing.set(job_class, job_class, disk, client, 1.0)
    model.link(routing)
    return model


def solve_table(populations, cpu_factor=1.0, disk_factor=1.0, network_factor=1.0):
    options = SolverOptions()
    options.method = "default"
    solver = SolverMVA(build_model(populations, cpu_factor, disk_factor, network_factor), options)
    with contextlib.redirect_stdout(StringIO()):
        return solver.get_avg_table()


def rows_for_class(table, cls):
    return table.data[
        (table.data["JobClass"] == cls)
        & (table.data["Station"].isin(["Ethernet LAN", "Server CPU", "Server disk"]))
    ]


def class_response(table, cls):
    return float(rows_for_class(table, cls)["RespT"].astype(float).sum())


def class_throughput(table, cls):
    return float(rows_for_class(table, cls)["Tput"].astype(float).iloc[0])


def station_util(table, station):
    return float(table.data.loc[table.data["Station"] == station, "Util"].astype(float).sum())


def summarize(table):
    return {
        "response": {cls: class_response(table, cls) for cls in CLASSES},
        "throughput": {cls: class_throughput(table, cls) for cls in CLASSES},
        "util": {
            "Ethernet LAN": station_util(table, "Ethernet LAN"),
            "Server CPU": station_util(table, "Server CPU"),
            "Server disk": station_util(table, "Server disk"),
        },
    }


def percent_change(new, old):
    return (new / old - 1.0) * 100.0


def find_minimum_single_upgrade(device):
    lo = 1.0
    hi = 2.0

    def result_for(factor):
        kwargs = {"cpu_factor": 1.0, "disk_factor": 1.0, "network_factor": 1.0}
        kwargs[device] = factor
        table = solve_table(DOUBLED_POPULATIONS, **kwargs)
        return table, summarize(table)

    table, summary = result_for(hi)
    while summary["response"]["Average"] > AVERAGE_RESPONSE_TARGET and hi < 64:
        hi *= 2.0
        table, summary = result_for(hi)

    if summary["response"]["Average"] > AVERAGE_RESPONSE_TARGET:
        return None, None, None

    best_table = table
    best_summary = summary
    for _ in range(25):
        mid = (lo + hi) / 2.0
        table, summary = result_for(mid)
        if summary["response"]["Average"] <= AVERAGE_RESPONSE_TARGET:
            hi = mid
            best_table = table
            best_summary = summary
        else:
            lo = mid
    return hi, best_table, best_summary


def find_minimum_combined_upgrade(devices):
    lo = 1.0
    hi = 2.0

    def result_for(factor):
        kwargs = {"cpu_factor": 1.0, "disk_factor": 1.0, "network_factor": 1.0}
        for device in devices:
            kwargs[device] = factor
        table = solve_table(DOUBLED_POPULATIONS, **kwargs)
        return table, summarize(table)

    table, summary = result_for(hi)
    while summary["response"]["Average"] > AVERAGE_RESPONSE_TARGET and hi < 64:
        hi *= 2.0
        table, summary = result_for(hi)

    if summary["response"]["Average"] > AVERAGE_RESPONSE_TARGET:
        return None, None, None

    best_table = table
    best_summary = summary
    for _ in range(25):
        mid = (lo + hi) / 2.0
        table, summary = result_for(mid)
        if summary["response"]["Average"] <= AVERAGE_RESPONSE_TARGET:
            hi = mid
            best_table = table
            best_summary = summary
        else:
            lo = mid
    return hi, best_table, best_summary


def print_summary(title, summary):
    print(title)
    print("Class     Response(sec)  Throughput(tps)")
    for cls in CLASSES:
        print(f"{cls:<9} {summary['response'][cls]:>12.6f}  {summary['throughput'][cls]:>14.6f}")
    print("Utilization")
    for station, util in summary["util"].items():
        print(f"{station}: {util:.6f}")


def main():
    base_table = solve_table(BASE_POPULATIONS)
    doubled_table = solve_table(DOUBLED_POPULATIONS)
    base = summarize(base_table)
    doubled = summarize(doubled_table)

    upgrades = {}
    for device in ["cpu_factor", "disk_factor", "network_factor"]:
        upgrades[device] = find_minimum_single_upgrade(device)
    combined_upgrades = {
        "cpu_disk": find_minimum_combined_upgrade(["cpu_factor", "disk_factor"]),
        "cpu_disk_network": find_minimum_combined_upgrade(
            ["cpu_factor", "disk_factor", "network_factor"]
        ),
    }
    recommendation_device = "cpu_disk"
    recommendation = combined_upgrades[recommendation_device]

    print("Dados da Sec. 7.7")
    print("Populacao original: Trivial=10, Average=20, Complex=5")
    print("Populacao dobrada: Trivial=20, Average=40, Complex=10")
    print("Limite assumido para Average response time: 2.0 sec")
    print()
    print_summary("Cenario original reproduzido pelo LINE Solver", base)
    print()
    print_summary("Cenario com numero de workstations dobrado", doubled)
    print()
    print("Variacao ao dobrar workstations")
    print("Class     Response_change  Throughput_change")
    for cls in CLASSES:
        print(
            f"{cls:<9} {percent_change(doubled['response'][cls], base['response'][cls]):>14.2f}%"
            f"  {percent_change(doubled['throughput'][cls], base['throughput'][cls]):>15.2f}%"
        )
    print()
    print("Single-device upgrade search for Average response <= 2 sec")
    labels = {
        "cpu_factor": "Server CPU",
        "disk_factor": "Server disk",
        "network_factor": "Ethernet LAN",
        "cpu_disk": "Server CPU and server disk",
        "cpu_disk_network": "Server CPU, server disk, and Ethernet LAN",
    }
    for device, (factor, _, summary) in upgrades.items():
        if factor is None:
            print(f"{labels[device]}: not enough as a single-device upgrade up to factor 64")
        else:
            print(
                f"{labels[device]}: factor={factor:.6f}, "
                f"Average response={summary['response']['Average']:.6f} sec, "
                f"Average throughput={summary['throughput']['Average']:.6f} tps"
            )
    print("Combined upgrade search for Average response <= 2 sec")
    for device, (factor, _, summary) in combined_upgrades.items():
        if factor is None:
            print(f"{labels[device]}: not enough up to factor 64")
        else:
            print(
                f"{labels[device]}: factor={factor:.6f}, "
                f"Average response={summary['response']['Average']:.6f} sec, "
                f"Average throughput={summary['throughput']['Average']:.6f} tps"
            )
    print(
        f"Recommended upgrade: {labels[recommendation_device]} "
        f"by factor {recommendation[0]:.6f}"
    )
    print()
    print("LINE Solver table for doubled scenario")
    print(doubled_table)


if __name__ == "__main__":
    main()


"""A saída mostra que, ao dobrar as workstations para 20 triviais, 40 médias e 10 complexas, os tempos de
  resposta sobem para 4,076 s, 4,521 s e 5,188 s, respectivamente, enquanto os throughputs passam para 0,454,
  1,631 e 0,495 tps. A LAN praticamente não é gargalo (Util = 0,00137), mas CPU e disco ficam bem carregados,
  com 73,42% e 88,11% de utilização. Como a resposta das transações médias excede 2 s, o modelo indica que
  upgrades isolados em CPU, disco ou LAN não resolvem; a recomendação é aumentar conjuntamente a capacidade
  da CPU e do disco do servidor em cerca de 1,307x, o que reduz a resposta média para 2,0 s mantendo o
  throughput da classe média em aproximadamente 1,818 tps."""