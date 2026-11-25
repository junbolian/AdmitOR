# IR: {"sets":{"U":"range(num_end_users)","L":"range(num_locations)","D":[0,1]},"params":{"num_end_users":"nonnegative integer from params","num_locations":"nonnegative integer from params","fixed_setup_cost":"real[L] from params","latency_matrix":"real[U,L] from params","user_coordinates":"real[U,D] from params; descriptive only","location_coordinates":"real[L,D] from params; descriptive only"},"variables":{"opened[L]":"binary","assigned[U,L]":"binary"},"constraints":["For every u in U: sum(assigned[u,l] for l in L) = 1","For every (u,l) in U x L: assigned[u,l] <= opened[l]"],"objective":"minimize sum(fixed_setup_cost[l]*opened[l] for l in L) + sum(latency_matrix[u,l]*assigned[u,l] for u in U for l in L)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_end_users = params["num_end_users"]
    num_locations = params["num_locations"]
    fixed_setup_cost = params["fixed_setup_cost"]
    latency_matrix = params["latency_matrix"]
    user_coordinates = params["user_coordinates"]
    location_coordinates = params["location_coordinates"]

    model = pyo.ConcreteModel()

    model.num_end_users = pyo.Param(
        initialize=num_end_users, within=pyo.NonNegativeIntegers
    )
    model.num_locations = pyo.Param(
        initialize=num_locations, within=pyo.NonNegativeIntegers
    )

    model.users = pyo.Set(initialize=range(num_end_users), ordered=True)
    model.locations = pyo.Set(initialize=range(num_locations), ordered=True)
    model.dimensions = pyo.Set(initialize=[0, 1], ordered=True)

    model.setup_cost = pyo.Param(
        model.locations,
        initialize=lambda _, loc: fixed_setup_cost[loc],
        within=pyo.Reals,
    )
    model.latency = pyo.Param(
        model.users,
        model.locations,
        initialize=lambda _, user, loc: latency_matrix[user][loc],
        within=pyo.Reals,
    )
    model.user_position = pyo.Param(
        model.users,
        model.dimensions,
        initialize=lambda _, user, dim: user_coordinates[user][dim],
        within=pyo.Reals,
    )
    model.location_position = pyo.Param(
        model.locations,
        model.dimensions,
        initialize=lambda _, loc, dim: location_coordinates[loc][dim],
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.locations, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.users, model.locations, domain=pyo.Binary
    )

    def exactly_one_center_rule(instance, user):
        return (
            sum(instance.assigned[user, loc] for loc in instance.locations)
            == 1
        )

    model.exactly_one_center = pyo.Constraint(
        model.users, rule=exactly_one_center_rule
    )

    def activation_link_rule(instance, user, loc):
        return instance.assigned[user, loc] <= instance.opened[loc]

    model.activation_link = pyo.Constraint(
        model.users, model.locations, rule=activation_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.setup_cost[loc] * model.opened[loc]
                for loc in model.locations
            )
            + sum(
                model.latency[user, loc] * model.assigned[user, loc]
                for user in model.users
                for loc in model.locations
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}