# IR: {"sets":{"S":"1..10 servers","R":"1..10 candidate racks"},"params":{"rack_power_capacity":"nonnegative scalar","rack_cooling_capacity":"nonnegative scalar","server_power_demand":"nonnegative vector indexed by S","server_cooling_demand":"nonnegative vector indexed by S"},"variables":{"x[s,r]":"binary; server s assigned to rack r","y[r]":"binary; rack r powered on"},"constraints":["sum(r in R) x[s,r] = 1 for each s in S","x[s,r] <= y[r] for each s in S, r in R","sum(s in S) server_power_demand[s]*x[s,r] <= rack_power_capacity*y[r] for each r in R","sum(s in S) server_cooling_demand[s]*x[s,r] <= rack_cooling_capacity*y[r] for each r in R"],"objective":"minimize sum(r in R) y[r]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _server_values(values):
    """Accept a mapping keyed by 1..10 (integers or strings), or a length-10 sequence."""
    if isinstance(values, Mapping):
        return {
            server: values[server] if server in values else values[str(server)]
            for server in range(1, 11)
        }

    if len(values) != 10:
        raise ValueError("Each server demand sequence must contain 10 values.")

    return {server: values[server - 1] for server in range(1, 11)}


def solve(params):
    model = pyo.ConcreteModel()

    model.servers = pyo.RangeSet(1, 10)
    model.racks = pyo.RangeSet(1, 10)

    model.rack_power_capacity = pyo.Param(
        initialize=params["rack_power_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.rack_cooling_capacity = pyo.Param(
        initialize=params["rack_cooling_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.server_power_demand = pyo.Param(
        model.servers,
        initialize=_server_values(params["server_power_demand"]),
        within=pyo.NonNegativeReals,
    )
    model.server_cooling_demand = pyo.Param(
        model.servers,
        initialize=_server_values(params["server_cooling_demand"]),
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.servers, model.racks, domain=pyo.Binary)
    model.y = pyo.Var(model.racks, domain=pyo.Binary)

    def assignment_rule(block, server):
        return sum(block.x[server, rack] for rack in block.racks) == 1

    model.server_assignment = pyo.Constraint(
        model.servers, rule=assignment_rule
    )

    def activation_rule(block, server, rack):
        return block.x[server, rack] <= block.y[rack]

    model.assignment_activation = pyo.Constraint(
        model.servers, model.racks, rule=activation_rule
    )

    def power_rule(block, rack):
        return (
            sum(
                block.server_power_demand[server] * block.x[server, rack]
                for server in block.servers
            )
            <= block.rack_power_capacity * block.y[rack]
        )

    model.power_limit = pyo.Constraint(model.racks, rule=power_rule)

    def cooling_rule(block, rack):
        return (
            sum(
                block.server_cooling_demand[server] * block.x[server, rack]
                for server in block.servers
            )
            <= block.rack_cooling_capacity * block.y[rack]
        )

    model.cooling_limit = pyo.Constraint(model.racks, rule=cooling_rule)

    model.total_racks = pyo.Objective(
        expr=sum(model.y[rack] for rack in model.racks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_racks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}