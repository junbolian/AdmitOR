# IR: {"sets":{"T":["horse","bicycle","handcart"],"A":["bicycle","handcart"]},"params":["demand","pollution_budget","pollution_per_horse_trip","pollution_per_bicycle_trip","pollution_per_handcart_trip","min_horse_trips","capacity_horse","capacity_bicycle","capacity_handcart"],"domains":"All inputs finite and nonnegative; capacities strictly positive.","derived":{"capacity[t]":"capacity_<t>","pollution[t]":"pollution_per_<t>_trip","U[a]":"ceil(demand/capacity[a])"},"variables":{"trips[t in T]":"NonNegativeIntegers","chosen[a in A]":"Binary"},"constraints":["sum(capacity[t]*trips[t] for t in T) >= demand","sum(pollution[t]*trips[t] for t in T) <= pollution_budget","trips[horse] >= min_horse_trips","sum(chosen[a] for a in A) == 1","trips[a] <= U[a]*chosen[a] for a in A"],"objective":{"sense":"minimize","expression":"sum(trips[t] for t in T)","assumption":"The problem omits an objective; minimize total trips."}}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = float(params["demand"])
    pollution_budget = float(params["pollution_budget"])
    pollution_per_horse_trip = float(params["pollution_per_horse_trip"])
    pollution_per_bicycle_trip = float(params["pollution_per_bicycle_trip"])
    pollution_per_handcart_trip = float(params["pollution_per_handcart_trip"])
    min_horse_trips = float(params["min_horse_trips"])
    capacity_horse = float(params["capacity_horse"])
    capacity_bicycle = float(params["capacity_bicycle"])
    capacity_handcart = float(params["capacity_handcart"])

    input_values = (
        demand,
        pollution_budget,
        pollution_per_horse_trip,
        pollution_per_bicycle_trip,
        pollution_per_handcart_trip,
        min_horse_trips,
        capacity_horse,
        capacity_bicycle,
        capacity_handcart,
    )
    if any(not math.isfinite(value) or value < 0 for value in input_values):
        return {"objective": None, "status": "invalid_parameters"}

    capacity_data = {
        "horse": capacity_horse,
        "bicycle": capacity_bicycle,
        "handcart": capacity_handcart,
    }
    if any(value <= 0 for value in capacity_data.values()):
        return {"objective": None, "status": "invalid_parameters"}

    pollution_data = {
        "horse": pollution_per_horse_trip,
        "bicycle": pollution_per_bicycle_trip,
        "handcart": pollution_per_handcart_trip,
    }

    # These bounds preserve an optimum: additional trips beyond those needed
    # to carry all demand cannot improve the objective or reduce pollution.
    alternative_bounds = {
        option: math.ceil(demand / capacity_data[option])
        for option in ("bicycle", "handcart")
    }

    model = pyo.ConcreteModel()
    model.transport_options = pyo.Set(
        initialize=("horse", "bicycle", "handcart"), ordered=True
    )
    model.alternatives = pyo.Set(
        initialize=("bicycle", "handcart"), ordered=True
    )

    model.required_demand = pyo.Param(initialize=demand)
    model.allowed_pollution = pyo.Param(initialize=pollution_budget)
    model.required_horse_trips = pyo.Param(initialize=min_horse_trips)
    model.trip_capacity = pyo.Param(
        model.transport_options, initialize=capacity_data
    )
    model.trip_pollution = pyo.Param(
        model.transport_options, initialize=pollution_data
    )
    model.alternative_trip_bound = pyo.Param(
        model.alternatives, initialize=alternative_bounds
    )

    model.trips = pyo.Var(
        model.transport_options, domain=pyo.NonNegativeIntegers
    )
    model.chosen = pyo.Var(model.alternatives, domain=pyo.Binary)

    model.demand_requirement = pyo.Constraint(
        expr=sum(
            model.trip_capacity[option] * model.trips[option]
            for option in model.transport_options
        )
        >= model.required_demand
    )
    model.pollution_limit = pyo.Constraint(
        expr=sum(
            model.trip_pollution[option] * model.trips[option]
            for option in model.transport_options
        )
        <= model.allowed_pollution
    )
    model.horse_requirement = pyo.Constraint(
        expr=model.trips["horse"] >= model.required_horse_trips
    )
    model.alternative_selection = pyo.Constraint(
        expr=sum(model.chosen[option] for option in model.alternatives) == 1
    )

    def alternative_link_rule(block, option):
        return (
            block.trips[option]
            <= block.alternative_trip_bound[option] * block.chosen[option]
        )

    model.alternative_link = pyo.Constraint(
        model.alternatives, rule=alternative_link_rule
    )
    model.total_trips = pyo.Objective(
        expr=sum(
            model.trips[option] for option in model.transport_options
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
        obj_val = float(pyo.value(model.total_trips))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}