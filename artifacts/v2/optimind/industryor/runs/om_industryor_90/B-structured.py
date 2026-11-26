# IR: {"sets":{"B":"range(num_buses_available)","S":"range(num_minibuses_available)"},"params":["students","bus_capacity","minibus_capacity","bus_cost","minibus_cost","num_buses_available","num_minibuses_available","num_drivers"],"variables":{"bus_used[b in B]":"Binary","minibus_used[s in S]":"Binary"},"expressions":{"total_seats":"bus_capacity*sum(bus_used)+minibus_capacity*sum(minibus_used)","total_vehicles":"sum(bus_used)+sum(minibus_used)"},"constraints":["total_seats >= students","total_vehicles <= num_drivers"],"objective":{"sense":"minimize","expression":"bus_cost*sum(bus_used)+minibus_cost*sum(minibus_used)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.students = pyo.Param(
        initialize=params["students"], within=pyo.NonNegativeIntegers
    )
    model.bus_capacity = pyo.Param(
        initialize=params["bus_capacity"], within=pyo.NonNegativeIntegers
    )
    model.minibus_capacity = pyo.Param(
        initialize=params["minibus_capacity"], within=pyo.NonNegativeIntegers
    )
    model.bus_cost = pyo.Param(
        initialize=params["bus_cost"], within=pyo.NonNegativeReals
    )
    model.minibus_cost = pyo.Param(
        initialize=params["minibus_cost"], within=pyo.NonNegativeReals
    )
    model.num_buses_available = pyo.Param(
        initialize=params["num_buses_available"],
        within=pyo.NonNegativeIntegers,
    )
    model.num_minibuses_available = pyo.Param(
        initialize=params["num_minibuses_available"],
        within=pyo.NonNegativeIntegers,
    )
    model.num_drivers = pyo.Param(
        initialize=params["num_drivers"], within=pyo.NonNegativeIntegers
    )

    model.B = pyo.Set(
        initialize=range(params["num_buses_available"]), ordered=True
    )
    model.S = pyo.Set(
        initialize=range(params["num_minibuses_available"]), ordered=True
    )

    model.bus_used = pyo.Var(model.B, domain=pyo.Binary)
    model.minibus_used = pyo.Var(model.S, domain=pyo.Binary)

    model.total_seats = pyo.Expression(
        expr=(
            model.bus_capacity
            * sum(model.bus_used[b] for b in model.B)
            + model.minibus_capacity
            * sum(model.minibus_used[s] for s in model.S)
        )
    )
    model.total_vehicles = pyo.Expression(
        expr=(
            sum(model.bus_used[b] for b in model.B)
            + sum(model.minibus_used[s] for s in model.S)
        )
    )

    model.seating_requirement = pyo.Constraint(
        expr=model.total_seats >= model.students
    )
    model.driver_limit = pyo.Constraint(
        expr=model.total_vehicles <= model.num_drivers
    )

    model.rental_cost = pyo.Objective(
        expr=(
            model.bus_cost * sum(model.bus_used[b] for b in model.B)
            + model.minibus_cost
            * sum(model.minibus_used[s] for s in model.S)
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.rental_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}