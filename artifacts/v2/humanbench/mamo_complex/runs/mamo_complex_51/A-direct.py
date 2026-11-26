import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    regions = [1, 2, 3, 4, 5, 6]

    supply = {i: params["supply"][i - 1] for i in regions}
    demand = {i: params["demand"][i - 1] for i in regions}

    cost = {}
    for i in regions:
        for j in regions:
            if i != j:
                cost[(i, j)] = params["cost_{}_to_{}".format(i, j)]

    model.regions = pyo.Set(initialize=regions)
    arcs = [(i, j) for i in regions for j in regions if i != j]
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.flow[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    over_supply = supply[1] + supply[2] + supply[3] + supply[4] + supply[5] + supply[6]
    total_demand = demand[1] + demand[2] + demand[3] + demand[4] + demand[5] + demand[6]

    if over_supply < total_demand:
        return {"objective": None, "status": "infeasible"}

    # Final stock face = supply - outflow + inflow. Must equal demand.
    def balance_rule(m, i):
        outflow = sum(m.flow[(i, j)] for j in regions if j != i)
        inflow = sum(m.flow[(j, i)] for j in regions if j != i)
        return supply[i] + inflow - outflow == demand[i]

    model.balance = pyo.Constraint(model.regions, rule=balance_rule)

    # Total outflow from a region cannot exceed its supply
    def outbound_rule(m, i):
        return sum(m.flow[(i, j)] for j in regions if j != i) <= supply[i]

    model.max_outbound = pyo.Constraint(model.regions, rule=outbound_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}