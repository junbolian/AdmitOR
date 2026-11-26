import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
    }

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(mdl, i):
        return sum(mdl.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[(i, j)] for i in cities if i != j) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)
    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ), with city 1 fixed as the depot for the ordering vars.
    model.u[1].fix(1)
    for i in cities:
        if i != 1:
            model.u[i].setlb(2)

    def mtz_rule(mdl, i, j):
        if i != 1 and j != 1 and i != j:
            return mdl.u[i] - mdl.u[j] + 4 * mdl.x[(i, j)] <= 3
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(arcs, rule=mtz_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible or unsolvable"}

    return {"objective": obj_val, "status": "optimal"}