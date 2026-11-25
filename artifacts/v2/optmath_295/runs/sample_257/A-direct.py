import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    route_costs = params["route_costs"]
    supply = params["supply_node0"]
    demand = params["demand_node7"]

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(route_costs[index] * mdl.x[arc] for index, arc in enumerate(arcs))

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Net balance: outflow - inflow
    def balance_rule(mdl, n):
        out_flow = sum(mdl.x[(n, j)] for j in nodes if j != n)
        in_flow = sum(mdl.x[(i, n)] for i in nodes if i != n)
        if n == 0:
            return out_flow - in_flow == supply
        elif n == 7:
            return out_flow - in_flow == -demand
        else:
            return out_flow - in_flow == 0

    model.balance = pyo.Constraint(model.N, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}