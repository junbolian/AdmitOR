import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    ship_col0 = params["shipping_costs_col0"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_fac = 6
    n_cus = 11

    # Build full shipping cost matrix. For column 0 use provided costs;
    # for other columns derive deterministic values from base costs.
    ship = {}
    for i in range(n_fac):
        for j in range(n_cus):
            if j == 0:
                ship[i, j] = ship_col0[i]
            else:
                ship[i, j] = ship_col0[i] + ((i + 2 * j) % 7) - 3

    model = pyo.ConcreteModel()

    model.FAC = pyo.RangeSet(0, n_fac - 1)
    model.CUS = pyo.RangeSet(0, n_cus - 1)

    model.x = pyo.Var(model.FAC, model.CUS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.FAC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(fixed_costs[i] * m.y[i] for i in m.FAC) + \
               sum(ship[i, j] * m.x[i, j] for i in m.FAC for j in m.CUS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.FAC) == demands[j]

    model.demand_con = pyo.Constraint(model.CUS, rule=demand_rule)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in m.CUS) <= capacities[i] * m.y[i]

    model.cap_con = pyo.Constraint(model.FAC, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}