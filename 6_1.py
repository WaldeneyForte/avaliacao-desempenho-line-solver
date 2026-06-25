"""
Questao 6.1

Enunciado:
Consider the transaction system of Sec. 6.2. Calculate the performance measures of that model using the approximate MVA algorithm. Assume that the stopping criterion is to have a maximum difference of 0.001 for successive values of n;,. Suppose now that the multiprogramming level of the update class
is tripled. Recalculate the model’s results using the exact and approximate
techniques. Compare the computational effort required by the two algorithms.
"""

from line_solver import *

import contextlib
import io
from itertools import product
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


def population_tuple(population):
    return tuple(population[class_name] for class_name in CLASSES)


def demand(station_index, class_index):
    return DEMANDS[STATIONS[station_index]][CLASSES[class_index]]


def exact_mva(population):
    target = population_tuple(population)
    station_count = len(STATIONS)
    class_count = len(CLASSES)
    q_by_state = {
        tuple(0 for _ in CLASSES): [
            [0.0 for _ in range(class_count)] for _ in range(station_count)
        ]
    }
    x_by_state = {}
    r_by_state = {}
    states_evaluated = 0

    ranges = [range(n + 1) for n in target]
    for state in product(*ranges):
        if sum(state) == 0:
            continue

        states_evaluated += 1
        q_state = [[0.0 for _ in range(class_count)] for _ in range(station_count)]
        x_state = [0.0 for _ in range(class_count)]
        r_state = [[0.0 for _ in range(class_count)] for _ in range(station_count)]

        for class_index, class_population in enumerate(state):
            if class_population == 0:
                continue

            previous_state = list(state)
            previous_state[class_index] -= 1
            previous_state = tuple(previous_state)
            q_previous = q_by_state[previous_state]

            total_response = 0.0
            for station_index in range(station_count):
                total_queue_previous = sum(q_previous[station_index])
                residence = demand(station_index, class_index) * (
                    1.0 + total_queue_previous
                )
                r_state[station_index][class_index] = residence
                total_response += residence

            x_state[class_index] = class_population / total_response

            for station_index in range(station_count):
                q_state[station_index][class_index] = (
                    x_state[class_index] * r_state[station_index][class_index]
                )

        q_by_state[state] = q_state
        x_by_state[state] = x_state
        r_by_state[state] = r_state

    return {
        "q": q_by_state[target],
        "x": x_by_state[target],
        "r": r_by_state[target],
        "states": states_evaluated,
    }


def approximate_mva(population, tolerance=TOLERANCE):
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
        r = [[0.0 for _ in range(class_count)] for _ in range(station_count)]
        x = [0.0 for _ in range(class_count)]
        q_new = [[0.0 for _ in range(class_count)] for _ in range(station_count)]

        for class_index, class_population in enumerate(n):
            total_response = 0.0
            for station_index in range(station_count):
                same_class_adjustment = (
                    q[station_index][class_index] / class_population
                    if class_population > 0
                    else 0.0
                )
                queue_seen = sum(q[station_index]) - same_class_adjustment
                residence = demand(station_index, class_index) * (1.0 + queue_seen)
                r[station_index][class_index] = residence
                total_response += residence

            x[class_index] = class_population / total_response

            for station_index in range(station_count):
                q_new[station_index][class_index] = (
                    x[class_index] * r[station_index][class_index]
                )

        max_difference = max(
            abs(q_new[i][r_index] - q[i][r_index])
            for i in range(station_count)
            for r_index in range(class_count)
        )
        q = q_new

        if max_difference <= tolerance:
            return {
                "q": q,
                "x": x,
                "r": r,
                "iterations": iterations,
                "max_difference": max_difference,
            }


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


def line_solver_table(population):
    options = SolverOptions()
    options.method = "exact"
    solver = SolverMVA(build_line_model(population), options)
    with contextlib.redirect_stdout(io.StringIO()):
        return solver.get_avg_table()


def summarize(result):
    rows = []
    for class_index, class_name in enumerate(CLASSES):
        class_response = sum(result["r"][i][class_index] for i in range(len(STATIONS)))
        class_queue = sum(result["q"][i][class_index] for i in range(len(STATIONS)))
        rows.append(
            {
                "class": class_name,
                "throughput": result["x"][class_index],
                "response": class_response,
                "queue": class_queue,
            }
        )
    return rows


def print_result(title, result):
    print(title)
    print("Class   Tput       RespT      QLen")
    for row in summarize(result):
        print(
            f"{row['class']:<7} "
            f"{row['throughput']:.6f}  "
            f"{row['response']:.6f}  "
            f"{row['queue']:.6f}"
        )

    print("Station/Class QLen")
    for station_index, station in enumerate(STATIONS):
        values = " ".join(
            f"{CLASSES[class_index]}={result['q'][station_index][class_index]:.6f}"
            for class_index in range(len(CLASSES))
        )
        print(f"{station:<6} {values}")


def run_scenario(name, population):
    print(f"\n{name}")
    print(f"Population: Query={population['Query']}, Update={population['Update']}")

    start = perf_counter()
    exact = exact_mva(population)
    exact_time = perf_counter() - start

    start = perf_counter()
    approximate = approximate_mva(population)
    approximate_time = perf_counter() - start

    print_result("Exact MVA", exact)
    print_result("Approximate MVA", approximate)

    print("Computational effort")
    print(f"Exact states evaluated: {exact['states']}")
    print(f"Exact runtime: {exact_time:.6f} s")
    print(f"Approximate iterations: {approximate['iterations']}")
    print(f"Approximate max difference: {approximate['max_difference']:.6f}")
    print(f"Approximate runtime: {approximate_time:.6f} s")

    print("LINE Solver exact table")
    print(line_solver_table(population))

    return exact, approximate, exact_time, approximate_time


original = run_scenario("Original Sec. 6.2 model", ORIGINAL_POPULATION)
tripled = run_scenario(
    "Update class multiprogramming tripled", TRIPLED_UPDATE_POPULATION
)


"""No modelo original da Sec. 6.2, com 3 queries e 1 update, a MVA exata deu throughput 4,093886 para Query e 0,409333 para Update; a MVA
  aproximada, com tolerância 0,001, convergiu em 9 iterações e estimou 3,996877 e 0,406923, respectivamente. Ao triplicar o MPL da classe
  Update para 3, a MVA exata deu throughput 2,938097 para Query e 0,906446 para Update; a aproximada convergiu em 12 iterações e estimou
  2,846144 e 0,898892. O esforço computacional da exata cresceu de 7 para 15 estados avaliados, enquanto a aproximada exigiu apenas algumas
  iterações, mantendo custo baixo; a aproximação ficou próxima da exata, mas subestimou principalmente o throughput da classe Query no cenário
  com mais updates."""