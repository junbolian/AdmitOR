import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    transport_cost = params["transport_cost"]
    node_net_demand = params["node_net_demand"]
    node_capacity = params["node_capacity"]
    link_capacity = params["link_capacity"]

    nodes = list(range(7))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def flow_balance_rule(m, i):
        inflow = sum(m.x[j, i] for j in nodes if j != i)
        outflow = sum(m.x[i, j] for j in nodes if j != i)
        return inflow - outflow == node_net_demand[i]

    model.flow_balance = pyo.Constraint(model.NODES, rule=flow_balance_rule)

    def recv_cap_rule(m, i):
        return sum(m.x[j, i] for j in nodes if j != i) <= node_capacity[i]

    model.recv_cap = pyo.Constraint(model.NODES, rule=recv_cap_rule)

    def link_cap_rule(m, i, j):
        return m.x[i, j] <= link_capacity[i * 6 + (j if j < i else j - 1)]

    model.link_cap = pyo.Constraint(model.ARCS, rule=link_cap_rule)

    def obj_rule(m):
        return sum(
            transport_cost[i * 6 + (j if j < i else j - 1)] * m.x[i, j]
            for (i, j) in arcs
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception as exc:
        return {"objective": None, "status": "solve_failed: " + str(exc)}

    return {"objective": obj_val, "status": "optimal"}