import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    net_supply = params["net_supply"]
    transport_cost = params["transport_cost"]
    node_capacity = params["node_capacity"]
    link_capacity = params["link_capacity"]

    n = len(net_supply)
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=list(range(n)))

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def link_cap_rule(model, i, j):
        return model.flow[i, j] <= link_capacity[arcs.index((i, j))]

    model.link_cap_con = pyo.Constraint(model.arcs, rule=link_cap_rule)

    def node_cap_rule(model, j):
        return sum(model.flow[i, j] for i in range(n) if i != j) <= node_capacity[j]

    model.node_cap_con = pyo.Constraint(model.nodes, rule=node_cap_rule)

    def balance_rule(model, k):
        outflow = sum(model.flow[k, j] for j in range(n) if j != k)
        inflow = sum(model.flow[i, k] for i in range(n) if i != k)
        return outflow - inflow == net_supply[k]

    model.balance_con = pyo.Constraint(model.nodes, rule=balance_rule)

    def obj_rule(model):
        return sum(transport_cost[arcs.index((i, j))] * model.flow[i, j]
                   for (i, j) in model.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}