# IR: {"sets":{"D":"0..18","S":"0..4"},"params":{"investment_cost":"S -> nonnegative real; params['investment_cost']","distance_matrix":"D x S -> nonnegative real; params['distance_matrix']"},"variables":{"open_site[s]":"binary","assigned[d,s]":"binary"},"constraints":["For each d in D: sum(assigned[d,s] for s in S) = 1","For each (d,s) in D x S: assigned[d,s] <= open_site[s]"],"objective":"Minimize sum(investment_cost[s]*open_site[s] for s in S) + sum(distance_matrix[d,s]*assigned[d,s] for d in D for s in S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    investment_cost = params["investment_cost"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.D = pyo.RangeSet(0, 18)
    model.S = pyo.RangeSet(0, 4)

    model.investment_cost = pyo.Param(
        model.S,
        initialize={site: investment_cost[site] for site in model.S},
        within=pyo.NonNegativeReals,
    )
    model.distance_matrix = pyo.Param(
        model.D,
        model.S,
        initialize={
            (driver, site): distance_matrix[driver][site]
            for driver in model.D
            for site in model.S
        },
        within=pyo.NonNegativeReals,
    )

    model.open_site = pyo.Var(model.S, domain=pyo.Binary)
    model.assigned = pyo.Var(model.D, model.S, domain=pyo.Binary)

    def exactly_one_station_rule(instance, driver):
        return sum(
            instance.assigned[driver, site] for site in instance.S
        ) == 1

    model.exactly_one_station = pyo.Constraint(
        model.D, rule=exactly_one_station_rule
    )

    def operational_station_rule(instance, driver, site):
        return instance.assigned[driver, site] <= instance.open_site[site]

    model.operational_station = pyo.Constraint(
        model.D, model.S, rule=operational_station_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.investment_cost[site] * model.open_site[site]
            for site in model.S
        )
        + sum(
            model.distance_matrix[driver, site] * model.assigned[driver, site]
            for driver in model.D
            for site in model.S
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}