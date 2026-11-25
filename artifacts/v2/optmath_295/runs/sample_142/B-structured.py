# IR: {"sets":{"F":"0..3","C":"0..9"},"params":{"fixed_cost":"params['fixed_cost'][f]","demand":"params['demand'][c]","capacity":"params['capacity'][f]","shipping_cost":"params['shipping_cost'][f][c]; all 40 entries required; never infer missing costs"},"variables":{"opened[f]":"Binary","shipped[f,c]":"NonNegativeReals"},"constraints":["For each c: sum_f shipped[f,c] == demand[c]","For each f: sum_c shipped[f,c] <= capacity[f]*opened[f]"],"objective":"minimize sum_f fixed_cost[f]*opened[f] + sum_f,c shipping_cost[f][c]*shipped[f,c]","input_validation":"Return missing_parameter or incomplete_parameter if required input data are absent; no optimization is possible without shipping costs."}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, index, prefix):
    """Read a sequence or mapping keyed by names or numeric indices."""
    if isinstance(data, Mapping):
        named_key = f"{prefix}_{index}"
        if named_key in data:
            return data[named_key]
        if index in data:
            return data[index]
        return data[str(index)]
    return data[index]


def solve(params):
    """
    Minimize facility opening and shipping costs.

    Required inputs:
        fixed_cost: Four facility costs.
        demand: Ten customer demands.
        capacity: Four facility capacities.
        shipping_cost: Complete four-by-ten matrix.

    Vectors and matrix rows may be sequences or mappings keyed by
    facility/customer names, integer indices, or string indices.
    Missing shipping costs are reported, never fabricated.
    """
    required_parameters = (
        "fixed_cost",
        "demand",
        "capacity",
        "shipping_cost",
    )
    for parameter_name in required_parameters:
        if parameter_name not in params or params[parameter_name] is None:
            return {
                "objective": None,
                "status": f"missing_parameter:{parameter_name}",
            }

    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    shipping_cost = params["shipping_cost"]

    facilities = range(4)
    customers = range(10)

    vector_inputs = (
        ("fixed_cost", fixed_cost, facilities, "facility"),
        ("demand", demand, customers, "customer"),
        ("capacity", capacity, facilities, "facility"),
    )
    normalized_vectors = {}
    for parameter_name, data, indices, prefix in vector_inputs:
        try:
            values = {
                position: _entry(data, position, prefix)
                for position in indices
            }
        except (KeyError, IndexError):
            return {
                "objective": None,
                "status": f"incomplete_parameter:{parameter_name}",
            }

        if any(value is None for value in values.values()):
            return {
                "objective": None,
                "status": f"incomplete_parameter:{parameter_name}",
            }
        normalized_vectors[parameter_name] = values

    try:
        shipping_values = {
            (facility, customer): _entry(
                _entry(shipping_cost, facility, "facility"),
                customer,
                "customer",
            )
            for facility in facilities
            for customer in customers
        }
    except (KeyError, IndexError):
        return {
            "objective": None,
            "status": "incomplete_parameter:shipping_cost",
        }

    if any(value is None for value in shipping_values.values()):
        return {
            "objective": None,
            "status": "incomplete_parameter:shipping_cost",
        }

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(0, 3)
    model.customers = pyo.RangeSet(0, 9)

    model.fixed_cost_data = pyo.Param(
        model.facilities,
        initialize=normalized_vectors["fixed_cost"],
        within=pyo.NonNegativeReals,
    )
    model.demand_data = pyo.Param(
        model.customers,
        initialize=normalized_vectors["demand"],
        within=pyo.NonNegativeReals,
    )
    model.capacity_data = pyo.Param(
        model.facilities,
        initialize=normalized_vectors["capacity"],
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost_data = pyo.Param(
        model.facilities,
        model.customers,
        initialize=shipping_values,
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, customer):
        return (
            sum(
                mdl.shipped[facility, customer]
                for facility in mdl.facilities
            )
            == mdl.demand_data[customer]
        )

    model.demand_balance = pyo.Constraint(
        model.customers,
        rule=demand_rule,
    )

    def capacity_rule(mdl, facility):
        return (
            sum(
                mdl.shipped[facility, customer]
                for customer in mdl.customers
            )
            <= mdl.capacity_data[facility] * mdl.opened[facility]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost_data[facility] * model.opened[facility]
            for facility in model.facilities
        )
        + sum(
            model.shipping_cost_data[facility, customer]
            * model.shipped[facility, customer]
            for facility in model.facilities
            for customer in model.customers
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