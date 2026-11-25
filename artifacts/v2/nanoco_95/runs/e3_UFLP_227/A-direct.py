import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_setup_cost = params["fixed_setup_cost"]
    latency_matrix = params["latency_matrix"]
    num_end_users = params["num_end_users"]
    num_locations = params["num_locations"]

    users = range(num_end_users)
    locations = range(num_locations)

    model = pyo.ConcreteModel()

    model.users = pyo.Set(initialize=list(users))
    model.locations = pyo.Set(initialize=list(locations))

    model.x = pyo.Var(model.users, model.locations, domain=pyo.Binary)
    model.y = pyo.Var(model.locations, domain=pyo.Binary)

    def obj_rule(m):
        assign_cost = sum(
            latency_matrix[i][j] * m.x[i, j]
            for i in m.users for j in m.locations
        )
        setup_cost = sum(
            fixed_setup_cost[j] * m.y[j]
            for j in m.locations
        )
        return assign_cost + setup_cost

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in m.locations) == 1

    model.assign_constraint = pyo.Constraint(model.users, rule=assign_rule)

    def link_rule(m, i, j):
        return m.x[i, j] <= m.y[j]

    model.link_constraint = pyo.Constraint(
        model.users, model.locations, rule=link_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}