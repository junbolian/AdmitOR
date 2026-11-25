# IR: {"sets":{"C":[0,1,2],"P":[0,1],"D":[0,1],"Z":[0,1,2,3]},"params":{"shipping_cost":"48 numeric entries, flattened in C,P,D,Z row-major order regardless of input nesting","fixed_cost_dc":"[D]","throughput_cost":"[D][Z]","plant_supply":"[P][C]","demand":"[C][Z]","dc_min_throughput":"[D]","dc_max_throughput":"[D]"},"variables":{"ship[C,P,D,Z]":"nonnegative continuous","opened[D]":"binary","assigned[D,Z]":"binary"},"expressions":{"zone_demand[Z]":"sum_c demand[c,z]","throughput[D]":"sum_z zone_demand[z]*assigned[d,z]"},"constraints":["sum_d assigned[d,z] = 1 for each z","assigned[d,z] <= opened[d] for each d,z","sum_d,z ship[c,p,d,z] <= plant_supply[p,c] for each p,c","sum_p ship[c,p,d,z] >= demand[c,z]*assigned[d,z] for each c,d,z","ship[c,p,d,z] <= plant_supply[p,c]*assigned[d,z] for each c,p,d,z","throughput[d] >= dc_min_throughput[d]*opened[d] for each d","throughput[d] <= dc_max_throughput[d]*opened[d] for each d"],"objective":"min sum_c,p,d,z shipping_cost[c,p,d,z]*ship[c,p,d,z] + sum_d fixed_cost_dc[d]*opened[d] + sum_d,z throughput_cost[d,z]*zone_demand[z]*assigned[d,z]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _flatten_numeric(values):
    """Flatten nested numeric arrays without assuming their grouping."""
    if isinstance(values, (list, tuple)):
        for item in values:
            yield from _flatten_numeric(item)
    elif hasattr(values, "ndim") and values.ndim > 0:
        for item in values:
            yield from _flatten_numeric(item)
    else:
        yield float(values)


def solve(params):
    shipping_entries = list(_flatten_numeric(params["shipping_cost"]))
    fixed_cost_dc = params["fixed_cost_dc"]
    throughput_cost = params["throughput_cost"]
    plant_supply = params["plant_supply"]
    demand = params["demand"]
    dc_min_throughput = params["dc_min_throughput"]
    dc_max_throughput = params["dc_max_throughput"]

    if len(shipping_entries) != 3 * 2 * 2 * 4:
        return {"objective": None, "status": "invalid_shipping_cost_shape"}

    shipping_cost = {}
    entry_iterator = iter(shipping_entries)
    for c in range(3):
        for p in range(2):
            for d in range(2):
                for z in range(4):
                    shipping_cost[c, p, d, z] = next(entry_iterator)

    model = pyo.ConcreteModel()
    model.C = pyo.RangeSet(0, 2)
    model.P = pyo.RangeSet(0, 1)
    model.D = pyo.RangeSet(0, 1)
    model.Z = pyo.RangeSet(0, 3)

    model.ship = pyo.Var(
        model.C, model.P, model.D, model.Z,
        domain=pyo.NonNegativeReals,
    )
    model.opened = pyo.Var(model.D, domain=pyo.Binary)
    model.assigned = pyo.Var(model.D, model.Z, domain=pyo.Binary)

    model.zone_demand = pyo.Expression(
        model.Z,
        rule=lambda mdl, z: sum(demand[c][z] for c in mdl.C),
    )
    model.throughput = pyo.Expression(
        model.D,
        rule=lambda mdl, d: sum(
            mdl.zone_demand[z] * mdl.assigned[d, z] for z in mdl.Z
        ),
    )

    model.zone_assignment = pyo.Constraint(
        model.Z,
        rule=lambda mdl, z: sum(mdl.assigned[d, z] for d in mdl.D) == 1,
    )
    model.assignment_open_link = pyo.Constraint(
        model.D,
        model.Z,
        rule=lambda mdl, d, z: mdl.assigned[d, z] <= mdl.opened[d],
    )
    model.supply_limit = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda mdl, p, c: sum(
            mdl.ship[c, p, d, z] for d in mdl.D for z in mdl.Z
        ) <= plant_supply[p][c],
    )
    model.demand_requirement = pyo.Constraint(
        model.C,
        model.D,
        model.Z,
        rule=lambda mdl, c, d, z: sum(
            mdl.ship[c, p, d, z] for p in mdl.P
        ) >= demand[c][z] * mdl.assigned[d, z],
    )
    model.shipment_assignment_link = pyo.Constraint(
        model.C,
        model.P,
        model.D,
        model.Z,
        rule=lambda mdl, c, p, d, z: (
            mdl.ship[c, p, d, z]
            <= plant_supply[p][c] * mdl.assigned[d, z]
        ),
    )
    model.minimum_throughput = pyo.Constraint(
        model.D,
        rule=lambda mdl, d: (
            mdl.throughput[d] >= dc_min_throughput[d] * mdl.opened[d]
        ),
    )
    model.maximum_throughput = pyo.Constraint(
        model.D,
        rule=lambda mdl, d: (
            mdl.throughput[d] <= dc_max_throughput[d] * mdl.opened[d]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                shipping_cost[c, p, d, z] * model.ship[c, p, d, z]
                for c in model.C
                for p in model.P
                for d in model.D
                for z in model.Z
            )
            + sum(
                fixed_cost_dc[d] * model.opened[d]
                for d in model.D
            )
            + sum(
                throughput_cost[d][z]
                * model.zone_demand[z]
                * model.assigned[d, z]
                for d in model.D
                for z in model.Z
            )
        ),
        sense=pyo.minimize,
    )

    # An infeasible solve may raise before a solution is loaded.
    # Success is determined only by subsequent objective evaluation.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}