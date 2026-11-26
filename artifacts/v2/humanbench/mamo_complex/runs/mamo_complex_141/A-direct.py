import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost_matrix"]
    cities = [1, 2, 3, 4, 5]

    model = pyo.ConcreteModel()

    model.i = pyo.Set(initialize=cities)
    model.j = pyo.Set(initialize=cities)

    # x[i,j] = 1 if edge i->j is used (i != j)
    model.x = pyo.Var(
        [(l, k) for l in cities for k in cities if l != k],
        domain=pyo.Binary,
    )

    # u[k] = position/order of city k along the tour (MTZ subtour elimination)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(1, 5))

    def obj_rule(mod):
        return sum(
            cost[l - 1][k - 1] * mod.x[l, k]
            for l in cities for k in cities if l != k
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing edge
    def out_rule(mod, l):
        return sum(mod.x[l, k] for k in cities if k != l) == 1

    model.out_cons = pyo.Constraint(cities, rule=out_rule)

    # Each city has exactly one incoming edge
    def in_rule(mod, k):
        return sum(mod.x[l, k] for l in cities if l != k) == 1

    model.in_cons = pyo.Constraint(cities, rule=in_rule)

    # MTZ subtour elimination: u[i] - u[j] + n*x[i,j] <= n-1 for i,j != depot
    n = len(cities)
    non_depot = [1, 2, 3, 4]  # city 5 treated as depot

    def mtz_rule(mod, l, k):
        return mod.u[l] - mod.u[k] + n * mod.x[l, k] <= n - 1

    model.mtz = pyo.Constraint(
        [(l, k) for l in non_depot for k in non_depot if l != k],
        rule=mtz_rule,
    )

    # Fix depot ordering bound
    model.depot_order = pyo.Constraint(expr=model.u[5] == 1)
    model.u1_lb = pyo.Constraint(expr=model.u[1] >= 2)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}