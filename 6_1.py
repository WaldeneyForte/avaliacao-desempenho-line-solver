"""
Questao 6.1

Enunciado:
Consider the transaction system of Sec. 6.2. Calculate the performance measures of that model using the approximate MVA algorithm. Assume that the stopping criterion is to have a maximum difference of 0.001 for successive values of n;,. Suppose now that the multiprogramming level of the update class
is tripled. Recalculate the model’s results using the exact and approximate
techniques. Compare the computational effort required by the two algorithms.
"""

from line_solver import *

import contextlib
from io import StringIO
from math import prod
from time import perf_counter


STATIONS = ["CPU", "Disk1", "Disk2"]
CLASSES = ["Query", "Update"]
DEMANDS = {
    "CPU": {"Query": 0.105, "Update": 0.375},
    "Disk1": {"Query": 0.180, "Update": 0.480},
    "Disk2": {"Query": 0.000, "Update": 0.240},
}
ORIGINAL_POPULATION = {"Query": 3, "Update": 1}
TRIPLED_UPDATE_POPULATION = {"Query": 3, "Update": 3}
TOLERANCE = 0.001


def build_line_model(population):
    model = Network("Sec 6.2 transaction system")

    cpu = Queue(model, "CPU", SchedStrategy.PS)
    disk1 = Queue(model, "Disk1", SchedStrategy.PS)
    disk2 = Queue(model, "Disk2", SchedStrategy.PS)

    query = ClosedClass(model, "Query", population["Query"], cpu)
    update = ClosedClass(model, "Update", population["Update"], cpu)

    cpu.set_service(query, Exp.fit_mean(DEMANDS["CPU"]["Query"]))
    disk1.set_service(query, Exp.fit_mean(DEMANDS["Disk1"]["Query"]))
    cpu.set_service(update, Exp.fit_mean(DEMANDS["CPU"]["Update"]))
    disk1.set_service(update, Exp.fit_mean(DEMANDS["Disk1"]["Update"]))
    disk2.set_service(update, Exp.fit_mean(DEMANDS["Disk2"]["Update"]))

    P = model.init_routing_matrix()
    P.set(query, query, cpu, disk1, 1.0)
    P.set(query, query, disk1, cpu, 1.0)
    P.set(update, update, cpu, disk1, 1.0)
    P.set(update, update, disk1, disk2, 1.0)
    P.set(update, update, disk2, cpu, 1.0)

    model.link(P)
    return model


def line_solver_table(population, method):
    options = SolverOptions()
    options.method = method
    options.iter_tol = TOLERANCE
    options.tol = TOLERANCE
    solver = SolverMVA(build_line_model(population), options)
    with contextlib.redirect_stdout(StringIO()):
        return solver.get_avg_table()


def population_tuple(population):
    return tuple(population[class_name] for class_name in CLASSES)


def demand(station_index, class_index):
    return DEMANDS[STATIONS[station_index]][CLASSES[class_index]]


def approximate_stopping_effort(population):
    n = population_tuple(population)
    station_count = len(STATIONS)
    class_count = len(CLASSES)
    q = [[0.0 for _ in range(class_count)] for _ in range(station_count)]

    for class_index, class_population in enumerate(n):
        class_demand_total = sum(demand(i, class_index) for i in range(station_count))
        for station_index in range(station_count):
            if class_demand_total > 0:
                q[station_index][class_index] = (
                    class_population
                    * demand(station_index, class_index)
                    / class_demand_total
                )

    iterations = 0
    while True:
        iterations += 1
        q_new = [[0.0 for _ in range(class_count)] for _ in range(station_count)]

        for class_index, class_population in enumerate(n):
            total_response = 0.0
            residence = [0.0 for _ in range(station_count)]

            for station_index in range(station_count):
                same_class_adjustment = (
                    q[station_index][class_index] / class_population
                    if class_population > 0
                    else 0.0
                )
                queue_seen = sum(q[station_index]) - same_class_adjustment
                residence[station_index] = demand(station_index, class_index) * (
                    1.0 + queue_seen
                )
                total_response += residence[station_index]

            throughput = class_population / total_response
            for station_index in range(station_count):
                q_new[station_index][class_index] = throughput * residence[station_index]

        max_difference = max(
            abs(q_new[i][r_index] - q[i][r_index])
            for i in range(station_count)
            for r_index in range(class_count)
        )
        q = q_new

        if max_difference <= TOLERANCE:
            return iterations, max_difference


def summarize_table(table):
    rows = []
    for class_name in CLASSES:
        class_rows = table.data[table.data["JobClass"] == class_name]
        rows.append(
            {
                "class": class_name,
                "throughput": float(class_rows["Tput"].iloc[0]),
                "response": float(class_rows["RespT"].sum()),
                "queue": float(class_rows["QLen"].sum()),
            }
        )
    return rows


def print_result(title, table):
    print(title)
    print("Class   Tput       RespT      QLen")
    for row in summarize_table(table):
        print(
            f"{row['class']:<7} "
            f"{row['throughput']:.6f}  "
            f"{row['response']:.6f}  "
            f"{row['queue']:.6f}"
        )

    print("Station/Class QLen")
    for station in STATIONS:
        values = []
        for class_name in CLASSES:
            rows = table.data[
                (table.data["Station"] == station)
                & (table.data["JobClass"] == class_name)
            ]
            qlen = 0.0 if rows.empty else float(rows["QLen"].iloc[0])
            values.append(f"{class_name}={qlen:.6f}")
        print(f"{station:<6} {' '.join(values)}")


def exact_state_count(population):
    return prod(population[class_name] + 1 for class_name in CLASSES) - 1


def run_scenario(name, population):
    print(f"\n{name}")
    print(f"Population: Query={population['Query']}, Update={population['Update']}")

    start = perf_counter()
    exact_table = line_solver_table(population, "exact")
    exact_time = perf_counter() - start

    start = perf_counter()
    approximate_table = line_solver_table(population, "amva.bs")
    approximate_time = perf_counter() - start

    approximate_iterations, approximate_max_difference = approximate_stopping_effort(
        population
    )

    print_result("Exact MVA - LINE Solver", exact_table)
    print_result("Approximate MVA - LINE Solver method amva.bs", approximate_table)

    print("Computational effort")
    print(f"Exact states evaluated: {exact_state_count(population)}")
    print(f"Exact LINE Solver runtime: {exact_time:.6f} s")
    print(f"Approximate stopping-check iterations: {approximate_iterations}")
    print(f"Approximate stopping-check max difference: {approximate_max_difference:.6f}")
    print(f"Approximate LINE Solver runtime: {approximate_time:.6f} s")

    print("LINE Solver exact table")
    print(exact_table)

    return exact_table, approximate_table, exact_time, approximate_time


original = run_scenario("Original Sec. 6.2 model", ORIGINAL_POPULATION)
tripled = run_scenario(
    "Update class multiprogramming tripled", TRIPLED_UPDATE_POPULATION
)
