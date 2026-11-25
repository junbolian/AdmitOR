# IR: {"sets":{"cities":[0,1,2,3],"nondepot":[1,2,3],"arcs":"(i,j) in cities x cities with i != j"},"params":{"cost_0_1":"travel cost 0->1","cost_0_2":"travel cost 0->2","cost_0_3":"travel cost 0->3","cost_1_0":"travel cost 1->0","cost_1_2":"travel cost 1->2","cost_1_3":"travel cost 1->3","cost_2_0":"travel cost 2->0","cost_2_1":"travel cost 2->1","cost_2_3":"travel cost 2->3","cost_3_0":"travel cost 3->0","cost_3_1":"travel cost 3->1","cost_3_2":"travel cost 3->2","u_bound_lower":"nondepot position lower bound","u_bound_upper":"nondepot position upper bound","u_city0":"fixed depot position"},"variables":{"x[i,j]":"binary for each arc","u[i]":"real for each city"},"constraints":["sum(x[i,j] for j != i) = 1 for each city i","sum(x[i,j] for i != j) = 1 for each city j","u[0] = u_city0","u_bound_lower <= u[i] <= u_bound_upper for each nondepot city i","u[i] - u[j] + 4*x[i,j] <= 3 for distinct nondepot cities i,j"],"objective":"minimize sum(cost_i_j*x[i,j] for each arc)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (3, 0): params["cost_3_0"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
    }
    position_lower = params["u_bound_lower"]
    position_upper = params["u_bound_upper"]
    depot_position = params["u_city0"]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.nondepot = pyo.Set(initialize=[1, 2, 3], ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.cities
            for j in model.cities
            if i != j
        ],
    )
    model.travel_cost = pyo.Param(model.arcs, initialize=costs)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def position_bounds(instance, city):
        if city == 0:
            return None, None
        return position_lower, position_upper

    model.u = pyo.Var(
        model.cities,
        domain=pyo.Reals,
        bounds=position_bounds,
    )
    model.u[0].fix(depot_position)

    def departure_rule(instance, city):
        return sum(
            instance.x[city, destination]
            for destination in instance.cities
            if destination != city
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(instance, city):
        return sum(
            instance.x[origin, city]
            for origin in instance.cities
            if origin != city
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    def sequencing_rule(instance, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            instance.u[origin]
            - instance.u[destination]
            + 4 * instance.x[origin, destination]
            <= 3
        )

    model.sequencing_constraints = pyo.Constraint(
        model.nondepot,
        model.nondepot,
        rule=sequencing_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}