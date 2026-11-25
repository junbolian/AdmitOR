import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    logistics_cost = params["logistics_cost"]

    n_fac = len(fixed_cost)
    n_cli = len(demand)

    facilities = list(range(1, n_fac + 1))
    clients = list(range(1, n_cli + 1))
    pairs = [(i, j) for i in clients for j in facilities]

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=clients)
    model.J = pyo.Set(initialize=facilities)
    model.IJ = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.IJ, domain=pyo.Binary)
    model.y = pyo.Var(model.J, domain=pyo.Binary)

    def obj_rule(m):
        return sum(fixed_cost[j - 1] * m.y[j] for j in m.J) + \
               sum(logistics_cost[i - 1][j - 1] * m.x[i, j] for (i, j) in m.IJ)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in m.J) == 1

    model.assign_con = pyo.Constraint(model.I, rule=assign_rule)

    def cap_rule(m, j):
        return sum(demand[i - 1] * m.x[i, j] for i in m.I) <= capacity[j - 1] * m.y[j]

    model.cap_con = pyo.Constraint(model.J, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}