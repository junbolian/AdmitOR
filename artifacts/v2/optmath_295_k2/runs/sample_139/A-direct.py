import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(5))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    net_flow = {
        0: params["net_flow_hub0"],
        1: params["net_flow_hub1"],
        2: params["net_flow_hub2"],
        3: params["net_flow_hub3"],
        4: params["net_flow_hub4"],
    }

    fixed_cost = {}
    capacity = {}
    var_cost = {}
    for (i, j) in arcs:
        if (i, j) == (0, 1):
            fixed_cost[(i, j)] = params["fixed_cost_0_1"]
            capacity[(i, j)] = params["capacity_0_1"]
            var_cost[(i, j)] = params["variable_cost_0_1"]
        elif (i, j) == (0, 2):
            fixed_cost[(i, j)] = params["fixed_cost_0_2"]
            capacity[(i, j)] = params["capacity_0_2"]
            var_cost[(i, j)] = params["variable_cost_0_2"]
        else:
            fixed_cost[(i, j)] = params["fixed_cost_other"]
            capacity[(i, j)] = params["capacity_other"]
            var_cost[(i, j)] = params["variable_cost_other"]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)
    model.build = pyo.Var(model.ARCS, domain=pyo.Binary)

    def capacity_rule(mdl, i, j):
        return mdl.flow[(i, j)] <= capacity[(i, j)] * mdl.build[(i, j)]

    model.capacity_link = pyo.Constraint(model.ARCS, rule=capacity_rule)

    def balance_rule(mdl, k):
        outflow = sum(mdl.flow[(k, j)] for j in nodes if j != k)
        inflow = sum(mdl.flow[(i, k)] for i in nodes if i != k)
        return outflow - inflow == net_flow[k]

    model.balance = pyo.Constraint(model.NODES, rule=balance_rule)

    def obj_rule(mdl):
        return sum(
            fixed_cost[(i, j)] * mdl.build[(i, j)]
            + var_cost[(i, j)] * mdl.flow[(i, j)]
            for (i, j) in arcs
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}