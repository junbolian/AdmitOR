import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(7))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost = {}
    for (i, j) in arcs:
        cost[(i, j)] = params["cost_{0}_{1}".format(i, j)]

    balance_param = params["balance_nodes_1_to_5"]
    if isinstance(balance_param, (list, tuple)):
        balance_list = list(balance_param)
    else:
        balance_list = [balance_param] * 5

    net = {}
    net[0] = params["supply_node_0"]
    net[6] = -params["demand_node_6"]
    for idx, k in enumerate(range(1, 6)):
        net[k] = -balance_list[idx]

    ub = params["route_usage_upper_bound"]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    model.balance = pyo.ConstraintList()
    for v in nodes:
        out_expr = sum(model.x[(v, j)] for j in nodes if j != v)
        in_expr = sum(model.x[(i, v)] for i in nodes if i != v)
        model.balance.add(out_expr - in_expr == net[v])

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}