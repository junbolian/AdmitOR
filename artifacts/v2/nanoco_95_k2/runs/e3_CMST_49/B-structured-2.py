# IR: {"sets":{"V":"{0,...,num_nodes-1}","T":"{1,...,num_turbines}","A":"{(i,j): i in V, j in T, i != j}"},"params":{"cost_matrix":"params['cost_matrix']; use upper triangle","num_nodes":"params['num_nodes']","num_turbines":"params['num_turbines']","K":"params['max_turbines_per_feeder']","c[i,j]":"cost_matrix[min(i,j)][max(i,j)]"},"variables":{"x[i,j]":"binary for (i,j) in A; selected parent-to-child arc","f[i,j]":"nonnegative continuous for (i,j) in A; downstream turbine count"},"constraints":["For each j in T: sum(i:(i,j) in A) x[i,j] = 1.","For each j in T: sum(i:(i,j) in A) f[i,j] - sum(k:(j,k) in A) f[j,k] = 1.","sum(j in T) f[0,j] = num_turbines.","For each (i,j) in A: f[i,j] <= K*x[i,j]."],"objective":"Minimize sum((i,j) in A) c[i,j]*x[i,j]."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_nodes = params["num_nodes"]
    num_turbines = params["num_turbines"]
    capacity = params["max_turbines_per_feeder"]

    if (
        not isinstance(num_nodes, int)
        or isinstance(num_nodes, bool)
        or not isinstance(num_turbines, int)
        or isinstance(num_turbines, bool)
        or num_turbines < 0
        or num_nodes != num_turbines + 1
        or capacity < 0
    ):
        return {"objective": None, "status": "invalid_parameters"}

    if len(cost_matrix) != num_nodes or any(
        len(row) != num_nodes for row in cost_matrix
    ):
        return {"objective": None, "status": "invalid_cost_matrix"}

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.T = pyo.Set(initialize=range(1, num_turbines + 1), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (source, target)
            for source in range(num_nodes)
            for target in range(1, num_turbines + 1)
            if source != target
        ],
        ordered=True,
    )

    model.capacity = pyo.Param(
        initialize=capacity, within=pyo.NonNegativeReals
    )
    model.turbine_count = pyo.Param(
        initialize=num_turbines, within=pyo.NonNegativeIntegers
    )
    model.cable_cost = pyo.Param(
        model.A,
        initialize={
            (source, target): cost_matrix[min(source, target)][max(source, target)]
            for source, target in model.A
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def parent_rule(instance, target):
        return sum(
            instance.x[source, target]
            for source in instance.V
            if source != target
        ) == 1

    model.one_parent = pyo.Constraint(model.T, rule=parent_rule)

    def turbine_flow_rule(instance, target):
        incoming = sum(
            instance.f[source, target]
            for source in instance.V
            if source != target
        )
        outgoing = sum(
            instance.f[target, child]
            for child in instance.T
            if child != target
        )
        return incoming - outgoing == 1

    model.turbine_flow_balance = pyo.Constraint(
        model.T, rule=turbine_flow_rule
    )

    model.root_flow_balance = pyo.Constraint(
        expr=sum(
            (model.f[0, target] for target in model.T),
            0 * model.turbine_count,
        ) == model.turbine_count
    )

    def capacity_rule(instance, source, target):
        return (
            instance.f[source, target]
            <= instance.capacity * instance.x[source, target]
        )

    model.arc_capacity = pyo.Constraint(model.A, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cable_cost[source, target] * model.x[source, target]
            for source, target in model.A
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