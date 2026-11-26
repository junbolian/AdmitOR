import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["A", "B", "C", "D"]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost_data = {
        ("A", "B"): params["cost_A_B"],
        ("A", "C"): params["cost_A_C"],
        ("A", "D"): params["cost_A_D"],
        ("B", "A"): params["cost_B_A"],
        ("B", "C"): params["cost_B_C"],
        ("B", "D"): params["cost_B_D"],
        ("C", "A"): params["cost_C_A"],
        ("C", "B"): params["cost_C_B"],
        ("C", "D"): params["cost_C_D"],
        ("D", "A"): params["cost_D_A"],
        ("D", "B"): params["cost_D_B"],
        ("D", "C"): params["cost_D_C"],
    }

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_data[(i, j)] * m.x[(i, j)] for (i, j) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1
    model.out_flow = pyo.Constraint(cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1
    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ-style) with continuous order variables.
    order = ["B", "C", "D"]

    def order_bounds(m, i):
        return (1, len(order))
    model.u = pyo.Var(order, domain=pyo.NonNegativeReals, bounds=order_bounds)

    def sec_rule(m, i, j):
        return m.u[i] - m.u[j] + len(order) * m.x[(i, j)] <= len(order) - 1
    model.sec = pyo.Constraint([(i, j) for i in order for j in order if i != j], rule=sec_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}