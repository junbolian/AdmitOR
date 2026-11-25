import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    node_net_outflow = params["node_net_outflow"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    nodes = list(range(7))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    arc_index = {a: k for k, a in enumerate(arcs)}

    fixed_cost_d = {a: fixed_cost[arc_index[a]] for a in arcs}
    variable_cost_d = {a: variable_cost[arc_index[a]] for a in arcs}
    capacity_d = {a: capacity[arc_index[a]] for a in arcs}

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.open = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(md, i):
        outflow = sum(md.flow[i, j] for j in nodes if j != i)
        inflow = sum(md.flow[j, i] for j in nodes if j != i)
        return outflow - inflow == node_net_outflow[i]

    model.balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    def capacity_rule(md, i, j):
        return md.flow[i, j] <= capacity_d[(i, j)] * md.open[i, j]

    model.cap = pyo.Constraint(model.arcs, rule=capacity_rule)

    def obj_rule(md):
        return (sum(fixed_cost_d[(i, j)] * md.open[i, j] for (i, j) in arcs)
                + sum(variable_cost_d[(i, j)] * md.flow[i, j] for (i, j) in arcs))

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}