import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]
    arcs = [(1, 2), (1, 3), (1, 4),
            (2, 1), (2, 3), (2, 4),
            (3, 1), (3, 2), (3, 4),
            (4, 1), (4, 2), (4, 3)]

    cost = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (2, 1): params["cost_21"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (3, 1): params["cost_31"],
        (3, 2): params["cost_32"],
        (3, 4): params["cost_34"],
        (4, 1): params["cost_41"],
        (4, 2): params["cost_42"],
        (4, 3): params["cost_43"],
    }

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.CITIES = pyo.Set(initialize=cities)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)
    model.u = pyo.Var(model.CITIES, domain=pyo.NonNegativeReals, bounds=(0, 3))

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_flow_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if (i, j) in arcs) == 1

    model.out_flow = pyo.Constraint(model.CITIES, rule=out_flow_rule)

    def in_flow_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if (i, j) in arcs) == 1

    model.in_flow = pyo.Constraint(model.CITIES, rule=in_flow_rule)

    def subtour_rule(m, i, j):
        if i != j and i >= 2 and j >= 2:
            return m.u[i] - m.u[j] + 3 * m.x[(i, j)] <= 2
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(model.CITIES, model.CITIES, rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}