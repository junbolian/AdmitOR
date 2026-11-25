# IR: {"sets":{"cities":[0,1,2,3],"others":[1,2,3],"arcs":"(i,j) in cities x cities with i!=j","order_pairs":"(i,j) in others x others with i!=j"},"params":{"cost":"params['cost'][i][j] for each arc","position_city0":"params['position_city0']","position_min_others":"params['position_min_others']","position_max_others":"params['position_max_others']"},"derived":{"big_M":"max(1,position_max_others-position_min_others+1)"},"variables":{"route[i,j]":"binary for each arc","position[i]":"integer for each city"},"constraints":["sum(route[i,j] for j!=i)=1 for each city i","sum(route[i,j] for i!=j)=1 for each city j","position[0]=position_city0","position_min_others<=position[i]<=position_max_others for each i in others","position[i]-position[j]+big_M*route[i,j]<=big_M-1 for each order_pair; arcs incident to city 0 are exempt"],"objective":{"sense":"minimize","expression":"sum(cost[i,j]*route[i,j] for each arc)"},"failure_handling":{"missing_parameter":"return objective=null,status=missing_parameter:<key>; never substitute example values","solver_no_feasible_solution":"return objective=null,status=no_feasible_solution","objective_unavailable":"return objective=null,status=objective_unavailable","unexpected_exception":"propagate"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Missing required inputs cannot be reconstructed without inventing data.
    # Handle absent keys explicitly instead of allowing a KeyError to crash.
    try:
        cost = params["cost"]
        position_city0 = params["position_city0"]
        position_min_others = params["position_min_others"]
        position_max_others = params["position_max_others"]
    except KeyError as exc:
        return {
            "objective": None,
            "status": f"missing_parameter:{exc.args[0]}",
        }

    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 3)
    model.others = pyo.RangeSet(1, 3)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(4)
            for j in range(4)
            if i != j
        ],
    )
    model.order_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, 4)
            for j in range(1, 4)
            if i != j
        ],
    )

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={(i, j): cost[i][j] for i, j in model.arcs},
        within=pyo.Reals,
    )
    model.root_position_value = pyo.Param(
        initialize=position_city0,
        within=pyo.Reals,
    )
    model.other_lower = pyo.Param(
        initialize=position_min_others,
        within=pyo.Reals,
    )
    model.other_upper = pyo.Param(
        initialize=position_max_others,
        within=pyo.Reals,
    )
    model.big_M = pyo.Param(
        initialize=max(
            1,
            position_max_others - position_min_others + 1,
        ),
        within=pyo.PositiveReals,
    )

    model.route = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(model.cities, domain=pyo.Integers)

    def outgoing_rule(instance, i):
        return sum(
            instance.route[i, j]
            for j in instance.cities
            if j != i
        ) == 1

    model.outgoing_routes = pyo.Constraint(
        model.cities,
        rule=outgoing_rule,
    )

    def incoming_rule(instance, j):
        return sum(
            instance.route[i, j]
            for i in instance.cities
            if i != j
        ) == 1

    model.incoming_routes = pyo.Constraint(
        model.cities,
        rule=incoming_rule,
    )

    model.fixed_root_position = pyo.Constraint(
        expr=model.position[0] == model.root_position_value
    )

    def position_bounds_rule(instance, i):
        return (
            instance.other_lower,
            instance.position[i],
            instance.other_upper,
        )

    model.position_limits = pyo.Constraint(
        model.others,
        rule=position_bounds_rule,
    )

    def subtour_rule(instance, i, j):
        return (
            instance.position[i]
            - instance.position[j]
            + instance.big_M * instance.route[i, j]
            <= instance.big_M - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.order_pairs,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.route[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {
                "objective": None,
                "status": "no_feasible_solution",
            }
        raise

    # Objective retrieval is the sole success test.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}