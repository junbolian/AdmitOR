# IR: {"scope":"Necessary-condition model using only explicitly supplied incidence and demand data; infeasibility certifies infeasibility of the full problem. A feasible result cannot determine the unspecified full problem.","sets":{"lines":["L_0","L_1","L_2","L_3","L_4","L_5","L_6","L_7","L_8","L_9","L_10","L_11"],"known_od_lines":["L_1","L_2","L_8","L_9","L_10"],"known_station_0_lines":["L_0","L_1","L_2","L_9","L_11"]},"params":["fixed_cost","operational_cost","penalty_cost","vehicle_time_per_frequency","total_vehicle_capacity","min_frequency_if_selected","max_frequency_if_selected","min_od_frequency","min_transfer_hub_lines","example_od_7_4_demand"],"variables":{"selected[line]":"binary","frequency[line]":"nonnegative real","unserved_7_4":"nonnegative real","hub_0":"binary"},"constraints":["frequency[line]>=min_frequency_if_selected*selected[line]","frequency[line]<=max_frequency_if_selected*selected[line]","sum(vehicle_time_per_frequency[line]*frequency[line])<=total_vehicle_capacity","sum(frequency[line] for line in known_od_lines)+unserved_7_4>=example_od_7_4_demand","sum(frequency[line] for line in known_od_lines)>=min_od_frequency","sum(selected[line] for line in known_station_0_lines)>=min_transfer_hub_lines*hub_0"],"objective":"minimize 0, to test necessary feasibility without inventing missing demands, incidence, or route topology","reporting":"Solver failure returns infeasible_or_solver_failed; feasible necessary conditions return insufficient_problem_data, never a spurious optimum for an incomplete problem."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # The statement omits fourteen OD demands, most incidence data, and
    # the route topology. These cannot be reconstructed from cost vectors.
    # Nevertheless, the explicitly stated constraints can already certify
    # infeasibility, so test them before reporting missing problem data.
    fixed_cost = params["fixed_cost"]
    operational_cost = params["operational_cost"]
    penalty_cost = params["penalty_cost"]
    vehicle_time = params["vehicle_time_per_frequency"]
    capacity = params["total_vehicle_capacity"]
    minimum_frequency = params["min_frequency_if_selected"]
    maximum_frequency = params["max_frequency_if_selected"]
    minimum_od_frequency = params["min_od_frequency"]
    minimum_hub_lines = params["min_transfer_hub_lines"]
    known_demand = params["example_od_7_4_demand"]

    # These costs are intentionally not used in the feasibility objective.
    # Optimizing a partial cost expression would not solve the stated problem.
    _ = fixed_cost, operational_cost, penalty_cost

    line_labels = tuple(f"L_{idx}" for idx in range(12))
    known_od_lines = ("L_1", "L_2", "L_8", "L_9", "L_10")
    station_zero_lines = ("L_0", "L_1", "L_2", "L_9", "L_11")

    def line_value(data, label):
        """Accept label-keyed maps, integer-keyed maps, or ordered sequences."""
        position = int(label.split("_")[1])
        if isinstance(data, dict):
            if label in data:
                return data[label]
            if position in data:
                return data[position]
            return data[str(position)]
        return data[position]

    model = pyo.ConcreteModel()
    model.lines = pyo.Set(initialize=line_labels, ordered=True)
    model.selected = pyo.Var(model.lines, domain=pyo.Binary)
    model.frequency = pyo.Var(model.lines, domain=pyo.NonNegativeReals)
    model.unserved_7_4 = pyo.Var(domain=pyo.NonNegativeReals)
    model.hub_0 = pyo.Var(domain=pyo.Binary)

    model.minimum_service = pyo.Constraint(
        model.lines,
        rule=lambda mdl, line: (
            mdl.frequency[line] >= minimum_frequency * mdl.selected[line]
        ),
    )
    model.maximum_service = pyo.Constraint(
        model.lines,
        rule=lambda mdl, line: (
            mdl.frequency[line] <= maximum_frequency * mdl.selected[line]
        ),
    )
    model.vehicle_limit = pyo.Constraint(
        expr=sum(
            line_value(vehicle_time, line) * model.frequency[line]
            for line in model.lines
        )
        <= capacity
    )
    model.known_demand_requirement = pyo.Constraint(
        expr=sum(model.frequency[line] for line in known_od_lines)
        + model.unserved_7_4
        >= known_demand
    )
    model.known_od_service_requirement = pyo.Constraint(
        expr=sum(model.frequency[line] for line in known_od_lines)
        >= minimum_od_frequency
    )
    model.known_hub_requirement = pyo.Constraint(
        expr=sum(model.selected[line] for line in station_zero_lines)
        >= minimum_hub_lines * model.hub_0
    )
    model.feasibility_objective = pyo.Objective(expr=0, sense=pyo.minimize)

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_solver_failed"}

    try:
        obj_val = float(pyo.value(model.feasibility_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    # obj_val concerns only the feasibility certificate, not the requested
    # total-cost optimum. Reporting it as the latter would be incorrect.
    return {"objective": None, "status": "insufficient_problem_data"}