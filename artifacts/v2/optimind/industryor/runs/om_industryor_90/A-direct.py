import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    students = params["students"]
    bus_capacity = params["bus_capacity"]
    minibus_capacity = params["minibus_capacity"]
    bus_cost = params["bus_cost"]
    minibus_cost = params["minibus_cost"]
    num_buses_available = params["num_buses_available"]
    num_minibuses_available = params["num_minibuses_available"]
    num_drivers = params["num_drivers"]

    model = pyo.ConcreteModel()

    model.buses = pyo.RangeSet(0, num_buses_available - 1)
    model.minibuses = pyo.RangeSet(0, num_minibuses_available - 1)

    model.x_bus = pyo.Var(model.buses, domain=pyo.NonNegativeIntegers, bounds=(0, 1))
    model.x_minibus = pyo.Var(model.minibuses, domain=pyo.NonNegativeIntegers, bounds=(0, 1))

    model.capacity = pyo.Constraint(
        expr=bus_capacity * sum(model.x_bus[i] for i in model.buses)
        + minibus_capacity * sum(model.x_minibus[j] for j in model.minibuses)
        >= students
    )

    model.drivers = pyo.Constraint(
        expr=sum(model.x_bus[i] for i in model.buses)
        + sum(model.x_minibus[j] for j in model.minibuses)
        <= num_drivers
    )

    model.cost = pyo.Objective(
        expr=bus_cost * sum(model.x_bus[i] for i in model.buses)
        + minibus_cost * sum(model.x_minibus[j] for j in model.minibuses),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}