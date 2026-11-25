import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3, 4, 5]
    arcs = [(0, 2), (0, 3), (1, 2), (1, 3), (2, 4), (2, 5),
            (3, 4), (3, 5), (0, 4), (0, 5), (1, 4), (1, 5)]

    supply = params["supply"]
    capacity = params["capacity"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes, ordered=True)
    model.ARCS = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    model.supply_param = pyo.Param(
        model.NODES,
        initialize={i: supply[i] for i in nodes},
        mutable=True,
    )
    model.cap_param = pyo.Param(
        model.ARCS,
        initialize={a: capacity[k] for k, a in enumerate(arcs)},
        mutable=True,
    )
    model.cost_param = pyo.Param(
        model.ARCS,
        initialize={a: cost[k] for k, a in enumerate(arcs)},
        mutable=True,
    )

    def cap_rule(mdl, a):
        return mdl.flow[a] <= mdl.cap_param[a]
    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    def flow_balance_rule(mdl, n):
        outflow = sum(mdl.flow[a] for a in arcs if a[0] == n)
        inflow = sum(mdl.flow[a] for a in arcs if a[1] == n)
        return outflow - inflow == mdl.supply_param[n]
    model.balance_con = pyo.Constraint(model.NODES, rule=flow_balance_rule)

    def obj_rule(mdl):
        return sum(mdl.cost_param[a] * mdl.flow[a] for a in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}