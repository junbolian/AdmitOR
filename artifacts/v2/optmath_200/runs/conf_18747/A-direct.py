import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = int(params["num_cities"])
    u_lower = params["u_lower"]
    u_upper = params["u_upper"]

    cities = list(range(num_cities))

    def cost(i, j):
        return params["travel_cost_{}_{}".format(i, j)]

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, bounds=(u_lower, u_upper))

    def obj_rule(m):
        return sum(cost(i, j) * m.x[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def depart_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1

    model.depart = pyo.Constraint(cities, rule=depart_rule)

    def arrive_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1

    model.arrive = pyo.Constraint(cities, rule=arrive_rule)

    def subtour_rule(m, i, j):
        if i != j and i != 0 and j != 0:
            n = num_cities
            return m.u[i] - m.u[j] + n * m.x[i, j] <= n - 1
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(arcs, rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}