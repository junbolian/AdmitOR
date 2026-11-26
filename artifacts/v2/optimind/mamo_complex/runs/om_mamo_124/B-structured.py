# IR: {"sets":{"C":[1,2,3,4,5],"A":"{(i,j) in C x C: i != j}","U":[2,3,4,5]},"params":["cost_12","cost_13","cost_14","cost_15","cost_21","cost_23","cost_24","cost_25","cost_31","cost_32","cost_34","cost_35","cost_41","cost_42","cost_43","cost_45","cost_51","cost_52","cost_53","cost_54","num_cities"],"validation":"num_cities == 5","decision_variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,num_cities-1] for i in U"},"constraints":["sum(x[i,j] for j in C if j != i) == 1 for i in C","sum(x[i,j] for i in C if i != j) == 1 for j in C","u[i]-u[j]+num_cities*x[i,j] <= num_cities-1 for distinct i,j in U"],"objective":"minimize sum(cost_ij*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    costs = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (1, 5): params["cost_15"],
        (2, 1): params["cost_21"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (2, 5): params["cost_25"],
        (3, 1): params["cost_31"],
        (3, 2): params["cost_32"],
        (3, 4): params["cost_34"],
        (3, 5): params["cost_35"],
        (4, 1): params["cost_41"],
        (4, 2): params["cost_42"],
        (4, 3): params["cost_43"],
        (4, 5): params["cost_45"],
        (5, 1): params["cost_51"],
        (5, 2): params["cost_52"],
        (5, 3): params["cost_53"],
        (5, 4): params["cost_54"],
    }

    if num_cities != 5:
        return {"objective": None, "status": "invalid_num_cities"}

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(1, 5)
    model.nonroot_cities = pyo.RangeSet(2, 5)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.cities
            for j in model.cities
            if i != j
        ],
    )
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.city_count = pyo.Param(initialize=num_cities)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.nonroot_cities,
        domain=pyo.Reals,
        bounds=(1, num_cities - 1),
    )

    def outgoing_rule(problem, i):
        return sum(
            problem.x[i, j] for j in problem.cities if j != i
        ) == 1

    def incoming_rule(problem, j):
        return sum(
            problem.x[i, j] for i in problem.cities if i != j
        ) == 1

    def subtour_rule(problem, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            problem.u[i]
            - problem.u[j]
            + problem.city_count * problem.x[i, j]
            <= problem.city_count - 1
        )

    model.outgoing = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )
    model.incoming = pyo.Constraint(
        model.cities, rule=incoming_rule
    )
    model.subtour_elimination = pyo.Constraint(
        model.nonroot_cities,
        model.nonroot_cities,
        rule=subtour_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # An infeasible solve can raise before loading a solution.
    # Objective retrieval is the sole success criterion.
    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "infeasible_or_failed"
                if solver_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}