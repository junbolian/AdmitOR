import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_origin = params["supply_origin"]
    demand_destination = params["demand_destination"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    num_origins = len(supply_origin)
    num_destinations = len(demand_destination)
    origins = list(range(num_origins))
    destinations = list(range(num_destinations))

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=origins)
    model.destinations = pyo.Set(initialize=destinations)
    model.links = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in origins for j in destinations],
    )

    model.x = pyo.Var(model.links, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j] for (i, j) in m.links)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in destinations) == supply_origin[i]

    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in origins) == demand_destination[j]

    model.demand_con = pyo.Constraint(model.destinations, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacity_matrix[i][j]

    model.cap_con = pyo.Constraint(model.links, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}