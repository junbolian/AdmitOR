import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    nodes = list(range(1, len(supply) + 1))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(m, i):
        outflow = sum(m.flow[i, j] for j in m.nodes if (i, j) in arcs)
        inflow = sum(m.flow[j, i] for j in m.nodes if (j, i) in arcs)
        return supply[i - 1] + inflow - outflow == demand[i - 1]
    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def objective_rule(m):
        return sum(transport_cost[i, j] * m.flow[i, j] for (i, j) in arcs)
    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}