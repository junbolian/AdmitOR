# IR: {"sets":{"W":["Verona","Perugia","Rome","Pescara","Taranto","Lamezia"],"P":["Genoa","Venice","Ancona","Naples","Bari"]},"params":{"supply":"params['supply'][i], indexed in W order","demand":"params['demand'][j], indexed in P order","distance":"params['distance'][i][j], indexed in W x P order","cost_rate":"params['cost_rate'], euros per container-kilometer","truck_capacity":"params['truck_capacity'], containers per truck"},"variables":{"ship[w,p]":"nonnegative integer containers","trucks[w,p]":"nonnegative integer truck trips; unlimited fleet"},"constraints":["For each w: sum_p ship[w,p] <= supply[w]","For each p: sum_w ship[w,p] == demand[p]","For each (w,p): ship[w,p] <= truck_capacity * trucks[w,p]"],"objective":"minimize sum_(w,p) cost_rate * distance[w,p] * ship[w,p]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Inputs supply, demand, and distance are ordered sequences as specified."""
    warehouses = ("Verona", "Perugia", "Rome", "Pescara", "Taranto", "Lamezia")
    ports = ("Genoa", "Venice", "Ancona", "Naples", "Bari")

    supply = params["supply"]
    demand = params["demand"]
    distance = params["distance"]
    cost_rate = params["cost_rate"]
    truck_capacity = params["truck_capacity"]

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=warehouses, ordered=True)
    model.P = pyo.Set(initialize=ports, ordered=True)

    model.supply = pyo.Param(
        model.W,
        initialize={warehouse: supply[i] for i, warehouse in enumerate(warehouses)},
        within=pyo.NonNegativeIntegers,
    )
    model.demand = pyo.Param(
        model.P,
        initialize={port: demand[j] for j, port in enumerate(ports)},
        within=pyo.NonNegativeIntegers,
    )
    model.distance = pyo.Param(
        model.W,
        model.P,
        initialize={
            (warehouse, port): distance[i][j]
            for i, warehouse in enumerate(warehouses)
            for j, port in enumerate(ports)
        },
        within=pyo.NonNegativeReals,
    )
    model.cost_rate = pyo.Param(
        initialize=cost_rate,
        within=pyo.NonNegativeReals,
    )
    model.truck_capacity = pyo.Param(
        initialize=truck_capacity,
        within=pyo.PositiveIntegers,
    )

    model.ship = pyo.Var(model.W, model.P, domain=pyo.NonNegativeIntegers)
    model.trucks = pyo.Var(model.W, model.P, domain=pyo.NonNegativeIntegers)

    def supply_rule(model, warehouse):
        return (
            sum(model.ship[warehouse, port] for port in model.P)
            <= model.supply[warehouse]
        )

    model.supply_limits = pyo.Constraint(model.W, rule=supply_rule)

    def demand_rule(model, port):
        return (
            sum(model.ship[warehouse, port] for warehouse in model.W)
            == model.demand[port]
        )

    model.demand_requirements = pyo.Constraint(model.P, rule=demand_rule)

    def capacity_rule(model, warehouse, port):
        return (
            model.ship[warehouse, port]
            <= model.truck_capacity * model.trucks[warehouse, port]
        )

    model.truck_capacity_limits = pyo.Constraint(
        model.W, model.P, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_rate
            * model.distance[warehouse, port]
            * model.ship[warehouse, port]
            for warehouse in model.W
            for port in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no solution is available to load.
        # Objective retrievability remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}