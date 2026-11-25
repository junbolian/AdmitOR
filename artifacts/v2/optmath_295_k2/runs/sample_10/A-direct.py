import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    nodes = list(range(7))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost = {}
    for i, j in arcs:
        cost[(i, j)] = params["arc_cost_%d_%d" % (i, j)]

    model.arc_index = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arc_index, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.x[(i, j)] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    supply = params["supply_node_0"]
    demand = params["demand_node_6"]

    model.supply_con = pyo.Constraint(
        expr=sum(model.x[(0, j)] for j in nodes if j != 0) == supply
    )
    model.demand_con = pyo.Constraint(
        expr=sum(model.x[(i, 6)] for i in nodes if i != 6) == demand
    )

    balance_exprs = {}
    for k in range(1, 6):
        balance_exprs[k] = (
            sum(model.x[(i, k)] for i in nodes if i != k)
            - sum(model.x[(k, j)] for j in nodes if j != k)
            == -params["balance_nodes_1_5"]
        )
    model.balance_con = pyo.Constraint(balance_exprs)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}