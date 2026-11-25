# IR: {"sets":{"cities":[0,1,2,3],"arcs":"(i,j) in cities x cities with i!=j","sequence_arcs":"(i,j) in arcs with j!=0"},"params":{"cost":"params['cost'][i][j] for (i,j) in arcs","position_city0":"params['position_city0']","position_min_others":"params['position_min_others']","position_max_others":"params['position_max_others']","L[i]":"position_city0 if i==0 else position_min_others","U[i]":"position_city0 if i==0 else position_max_others","M[i,j]":"U[i]-L[j]+1"},"validation":"Return objective=null and status=missing_parameter:<key> if a required parameter is absent; do not substitute hardcoded data.","variables":{"route[i,j]":"binary for (i,j) in arcs","position[i]":"integer with L[i]<=position[i]<=U[i]"},"constraints":{"outgoing":"sum(route[i,j] for j!=i)=1 for each i","incoming":"sum(route[i,j] for i!=j)=1 for each j","root_position":"position[0]=position_city0","sequence":"position[j]>=position[i]+1-M[i,j]*(1-route[i,j]) for (i,j) in sequence_arcs; return arcs to City 0 are exempt"},"objective":"minimize sum(cost[i,j]*route[i,j] for (i,j) in arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    required_keys = (
        "cost",
        "position_city0",
        "position_min_others",
        "position_max_others",
    )
    for key in required_keys:
        if key not in params:
            return {
                "objective": None,
                "status": f"missing_parameter:{key}",
            }

    # A missing cost matrix cannot be reconstructed without violating
    # the requirement to obtain every numeric input from params.
    cost = params["cost"]
    position_city0 = params["position_city0"]
    position_min_others = params["position_min_others"]
    position_max_others = params["position_max_others"]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(4), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(4)
            for j in range(4)
            if i != j
        ],
    )
    model.sequence_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i, j in model.arcs
            if j != 0
        ],
    )

    model.cost = pyo.Param(
        model.arcs,
        initialize={(i, j): cost[i][j] for i, j in model.arcs},
        within=pyo.Reals,
    )
    model.position_city0 = pyo.Param(
        initialize=position_city0,
        within=pyo.Integers,
    )
    model.position_min_others = pyo.Param(
        initialize=position_min_others,
        within=pyo.Integers,
    )
    model.position_max_others = pyo.Param(
        initialize=position_max_others,
        within=pyo.Integers,
    )

    def position_bounds(model, i):
        if i == 0:
            return model.position_city0, model.position_city0
        return model.position_min_others, model.position_max_others

    model.route = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.cities,
        domain=pyo.Integers,
        bounds=position_bounds,
    )

    model.root_position = pyo.Constraint(
        expr=model.position[0] == model.position_city0
    )

    def outgoing_rule(model, i):
        return sum(
            model.route[i, j] for j in model.cities if j != i
        ) == 1

    model.outgoing = pyo.Constraint(
        model.cities,
        rule=outgoing_rule,
    )

    def incoming_rule(model, j):
        return sum(
            model.route[i, j] for i in model.cities if i != j
        ) == 1

    model.incoming = pyo.Constraint(
        model.cities,
        rule=incoming_rule,
    )

    def sequence_rule(model, i, j):
        upper_i = (
            model.position_city0
            if i == 0
            else model.position_max_others
        )
        lower_j = model.position_min_others
        big_m = upper_i - lower_j + 1
        return (
            model.position[j]
            >= model.position[i] + 1
            - big_m * (1 - model.route[i, j])
        )

    model.sequence = pyo.Constraint(
        model.sequence_arcs,
        rule=sequence_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.route[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "solve_failed" if solve_failed else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}