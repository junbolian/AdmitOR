import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    crew_capacities = params["crew_capacities"]
    fuel_costs = params["fuel_costs"]
    operating_costs = params["operating_costs"]

    n_crews = len(crew_capacities)
    n_zones = len(operating_costs[0])

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_crews - 1)
    model.J = pyo.RangeSet(0, n_zones - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def obj_rule(m):
        return sum(
            operating_costs[i][j] * m.x[i, j]
            for i in m.I
            for j in m.J
        )
    model.total_operating_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == 1
    model.assign_constraint = pyo.Constraint(model.J, rule=assign_rule)

    def capacity_rule(m, i):
        return sum(fuel_costs[i][j] * m.x[i, j] for j in m.J) <= crew_capacities[i]
    model.capacity_constraint = pyo.Constraint(model.I, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_operating_cost))
    return {"objective": obj_val, "status": "optimal"}