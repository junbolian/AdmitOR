import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]
    num_jobs = params["num_jobs"]
    num_stations = params["num_stations"]

    jobs = list(range(num_jobs))
    stations = list(range(num_stations))

    model = pyo.ConcreteModel()

    model.J = pyo.Set(initialize=jobs)
    model.S = pyo.Set(initialize=stations)

    # Completion time of job j on station s
    model.C = pyo.Var(model.J, model.S, domain=pyo.NonNegativeReals)

    # Makespan
    model.Cmax = pyo.Var(domain=pyo.NonNegativeReals)

    # Sequenced pairs on each station (precedence: job i before job k)
    model.P = pyo.Set(initialize=[(i, k) for i in jobs for k in jobs if i != k])

    model.y = pyo.Var(model.S, model.P, domain=pyo.Binary)

    def obj_rule(m):
        return m.Cmax

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def makespan_rule(m, j, s):
        if s == num_stations - 1:
            return m.C[j, s] <= m.Cmax
        return pyo.Constraint.Skip

    model.makespan_con = pyo.Constraint(model.J, model.S, rule=makespan_rule)

    def station_precedence_rule(m, j, s):
        if s == 0:
            return pyo.Constraint.Skip
        return m.C[j, s] >= m.C[j, s - 1] + processing_times[j][s]

    model.station_precedence = pyo.Constraint(model.J, model.S, rule=station_precedence_rule)

    def first_station_rule(m, j):
        return m.C[j, 0] >= processing_times[j][0]

    model.first_station = pyo.Constraint(model.J, rule=first_station_rule)

    def disjunctive_rule(m, s, i, k):
        return m.C[i, s] + processing_times[k][s] <= m.C[k, s] + m.y[s, i, k] * 1e6

    model.disjunctive = pyo.Constraint(model.S, model.P, rule=disjunctive_rule)

    def order_rule(m, s, i, k):
        if i < k:
            return m.y[s, i, k] + m.y[s, k, i] == 1
        return pyo.Constraint.Skip

    model.order = pyo.Constraint(model.S, model.P, rule=order_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}