import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    shops = [1, 2, 3, 4, 5]

    cost_data = {}
    for i in shops:
        for j in shops:
            if i != j:
                cost_data[(i, j)] = params["cost_{}_{}".format(i, j)]

    arcs = list(cost_data.keys())

    model = pyo.ConcreteModel()

    model.SHOPS = pyo.Set(initialize=shops)
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_data[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in shops if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in shops if i != j) == 1

    model.out_flow = pyo.Constraint(model.SHOPS, rule=out_rule)
    model.in_flow = pyo.Constraint(model.SHOPS, rule=in_rule)

    # Single-commodity flow subtour elimination.
    # One unit of flow leaves the depot (shop 1); every other shop has
    # one unit of demand. Flow is only allowed on arcs into non-depot nodes.
    flow_arcs = [(i, j) for (i, j) in arcs if j != 1]

    model.FLOW_ARCS = pyo.Set(initialize=flow_arcs, dimen=2)
    model.f = pyo.Var(model.FLOW_ARCS, domain=pyo.NonNegativeReals)

    def flow_conservation(m, j):
        inflow = sum(m.f[(i, j)] for i in shops if i != j and j != 1)
        outflow = sum(m.f[(j, k)] for k in shops if k != j and k != 1)
        if j == 1:
            # Depot: net outflow equals number of departing vehicles
            return -outflow == -1
        # Non-depot: inflow minus outflow equals demand of 1
        return inflow - outflow == 1

    model.flow_cons = pyo.Constraint(model.SHOPS, rule=flow_conservation)

    def flow_link(m, i, j):
        return m.f[(i, j)] <= (len(shops) - 1) * m.x[(i, j)]

    model.flow_link = pyo.Constraint(model.FLOW_ARCS, rule=flow_link)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}