import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 6
    cities = list(range(1, n + 1))

    cost_pairs = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (1, 5): params["cost_15"],
        (1, 6): params["cost_16"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (2, 5): params["cost_25"],
        (2, 6): params["cost_26"],
        (3, 4): params["cost_34"],
        (3, 5): params["cost_35"],
        (3, 6): params["cost_36"],
        (4, 5): params["cost_45"],
        (4, 6): params["cost_46"],
        (5, 6): params["cost_56"],
    }

    def cost(i, j):
        if i == j:
            return 0
        return cost_pairs[(min(i, j), max(i, j))]

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals)

    def objective_rule(m):
        return sum(cost(i, j) * m.x[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)
    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    model.u[1].fix(1)

    def subtour_rule(m, i, j):
        if i != j and i != 1 and j != 1:
            return m.u[i] - m.u[j] + n * m.x[i, j] <= n - 1
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(arcs, rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}