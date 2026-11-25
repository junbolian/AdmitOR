# IR: {"sets":{"I":"range(params['num_neighborhoods'])","J":"range(params['num_candidates'])"},"params":{"fixed_cost":"cost[j], j in J, from params['fixed_cost']","distance_cost":"cost[i][j], (i,j) in I x J, from params['distance_cost']","num_neighborhoods":"from params['num_neighborhoods']","num_candidates":"from params['num_candidates']"},"variables":{"leased[j]":"Binary, j in J","assigned[i,j]":"Binary, (i,j) in I x J"},"constraints":["sum(assigned[i,j] for j in J) == 1 for each i in I","assigned[i,j] <= leased[j] for each (i,j) in I x J"],"objective":"minimize sum(fixed_cost[j]*leased[j] for j in J) + sum(distance_cost[i][j]*assigned[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_neighborhoods = params["num_neighborhoods"]
    num_candidates = params["num_candidates"]
    fixed_cost = params["fixed_cost"]
    distance_cost = params["distance_cost"]

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=range(num_neighborhoods), ordered=True)
    model.J = pyo.Set(initialize=range(num_candidates), ordered=True)

    model.lease_cost = pyo.Param(
        model.J,
        initialize={j: fixed_cost[j] for j in model.J},
        within=pyo.Reals,
    )
    model.delivery_cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): distance_cost[i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.Reals,
    )

    model.leased = pyo.Var(model.J, domain=pyo.Binary)
    model.assigned = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def assignment_rule(instance, i):
        return (
            sum(instance.assigned[i, j] for j in instance.J)
            == 1
        )

    model.exactly_one_warehouse = pyo.Constraint(
        model.I,
        rule=assignment_rule,
    )

    def leasing_rule(instance, i, j):
        return instance.assigned[i, j] <= instance.leased[j]

    model.assignment_requires_lease = pyo.Constraint(
        model.I,
        model.J,
        rule=leasing_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.lease_cost[j] * model.leased[j]
                for j in model.J
            )
            + sum(
                model.delivery_cost[i, j] * model.assigned[i, j]
                for i in model.I
                for j in model.J
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}