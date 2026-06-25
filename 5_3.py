#What is the performance (utilizations, throughputs, queue lengths, and wait
#times of each device) of the original system proposed by the motivating example
#in Sec. 5.3?

from line_solver import Network, Queue, ClosedClass, SchedStrategy, Exp, SolverMVA

model = Network("Database workstation")

cpu = Queue(model, "CPU", SchedStrategy.FCFS)
fast = Queue(model, "FastDisk", SchedStrategy.FCFS)
slow = Queue(model, "SlowDisk", SchedStrategy.FCFS)

users = ClosedClass(model, "Users", 2, cpu)

cpu.set_service(users, Exp.fit_mean(10.0))
fast.set_service(users, Exp.fit_mean(20.0))
slow.set_service(users, Exp.fit_mean(30.0))

P = model.init_routing_matrix()
P.set(users, users, cpu, fast, 0.5)
P.set(users, users, cpu, slow, 0.5)
P.set(users, users, fast, cpu, 1.0)
P.set(users, users, slow, cpu, 1.0)

model.link(P)

solver = SolverMVA(model)
print(solver.get_avg_table())


#A saída mostra o desempenho do sistema original com dois usuários ativos. A CPU apresenta utilização de aproximadamente 42,42%, com throughput de 0,042424 transações por segundo e tamanho médio de fila de 0,54545 jobs. O disco rápido também possui utilização de 42,42%, porém seu throughput é 0,021212 jobs/s, pois é acessado apenas em metade das transações. Já o disco lento apresenta a maior utilização, 63,64%, além do maior tamanho médio de fila, 0,90909, e do maior tempo médio de resposta, 42,857 s. Isso indica que o disco lento é o principal gargalo do sistema, pois concentra maior tempo de espera e maior ocupação em comparação aos demais dispositivos. Como a soma dos tamanhos médios de fila é aproximadamente 2, o resultado é consistente com a população fechada de dois usuários no sistema.