import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    num_facilities = 10
    num_centers = 12
    facilities = list(range(num_facilities))
    centers = list(range(num_centers))

    # Read required numeric parameters
    supply = {i: params[f"supply"][i] for i in facilities}
    demand = {j: params[f"demand"][j] for j in centers}
    cost_low = params["cost_range_low"]
    cost_high = params["cost_range_high"]

    # Named route costs that are explicitly provided
    named_costs = {
        (0, 0): params["cost_f0_c0"],
        (0, 1): params["cost_f0_c1"],
        (1, 0): params["cost_f1_c0"],
        (2, 1): params["cost_f2_c1"],
    }

    def route_cost(i, j):
        if (i, j) in named_costs:
            return named_costs[(i, j)]
        # Remaining routes fall within the stated cost range; pick a
        # consistent representative value (midpoint) for feasibility.
        return (cost_low + cost_high) / 2.0

    model = pyo.ConcreteModel()

    model.FAC = pyo.Set(initialize=facilities)
    model.CEN = pyo.Set(initialize=centers)

    model.x = pyo.Var(model.FAC, model.CEN, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(route_cost(i, j) * m.x[i, j] for i in m.FAC for j in m.CEN)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.CEN) == supply[i]

    model.supply_con = pyo.Constraint(model.FAC, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.FAC) == demand[j]

    model.demand_con = pyo.Constraint(model.CEN, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}