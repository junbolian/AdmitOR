import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost_data = {
        (1, 2): params["c12"],
        (1, 3): params["c13"],
        (1, 4): params["c14"],
        (2, 1): params["c21"],
        (2, 3): params["c23"],
        (2, 4): params["c24"],
        (3, 1): params["c31"],
        (3, 2): params["c32"],
        (3, 4): params["c34"],
        (4, 1): params["c41"],
        (4, 2): params["c42"],
        (4, 3): params["c43"],
    }

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    # Each city entered exactly once
    model.in_flow = pyo.Constraint(
        model.cities,
        rule=lambda mm, j: sum(mm.x[i, j] for i in cities if i != j) == 1,
    )

    # Each city left exactly once
    model.out_flow = pyo.Constraint(
        model.cities,
        rule=lambda mm, i: sum(mm.x[i, j] for j in cities if j != i) == 1,
    )

    # Subtour elimination via MTZ for nodes {2,3,4} (anchor node 1)
    order_cities = [2, 3, 4]
    model.u = pyo.Var(order_cities, domain=pyo.NonNegativeReals)

    def mtz_rule(mm, i, j):
        if i == 1 or j == 1:
            return pyo.Constraint.Skip
        return mm.u[i] - mm.u[j] + 3 * mm.x[i, j] <= 2

    model.mtz = pyo.Constraint(
        [(i, j) for i in order_cities for j in order_cities if i != j],
        rule=mtz_rule,
    )

    model.u_bounds = pyo.Constraint(
        order_cities,
        rule=lambda mm, i: pyo.inequality(1, mm.u[i], 3),
    )

    def obj_rule(mm):
        return sum(cost_data[i, j] * mm.x[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}