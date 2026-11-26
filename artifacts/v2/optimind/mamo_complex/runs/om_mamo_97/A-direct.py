import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 6
    cities = list(range(1, n + 1))

    def get_cost(i, j):
        if i == j:
            return 0.0
        a, b = min(i, j), max(i, j)
        return params[f"cost_{a}_{b}"]

    cost = {(i, j): get_cost(i, j) for i in cities for j in cities}

    model = pyo.ConcreteModel()
    model.x = pyo.Var(cities, cities, domain=pyo.Binary)
    model.z = pyo.Var(range(2, n + 1), domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    model.cost_expr = pyo.Expression(
        expr=sum(cost[i, j] * model.x[i, j] for i in cities for j in cities if i != j)
    )

    def out_rule(md, i):
        return sum(md.x[i, j] for j in cities if j != i) == 1
    model.out_con = pyo.Constraint(cities, rule=out_rule)

    def in_rule(md, j):
        return sum(md.x[i, j] for i in cities if i != j) == 1
    model.in_con = pyo.Constraint(cities, rule=in_rule)

    # MTZ subtour elimination for nodes 2..n
    def mtz_rule(md, i, j):
        if i != j and i >= 2 and j >= 2:
            return md.z[i] - md.z[j] + n * md.x[i, j] <= n - 1
        return pyo.Constraint.Skip
    model.mtz_con = pyo.Constraint(cities, cities, rule=mtz_rule)

    def obj_rule(md):
        return md.cost_expr
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}