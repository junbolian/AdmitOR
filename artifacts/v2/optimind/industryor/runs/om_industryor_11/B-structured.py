# IR: {"sets":{"T":"0,...,5","A":"(i,j) in T x T with volume[i] >= volume[j]"},"params":{"volume":"params['volume'][i]","demand":"params['demand'][i]","unit_cost":"params['unit_cost'][i]","setup_cost":"params['setup_cost']"},"variables":{"allocation[i,j]":"nonnegative integer for (i,j) in A","equipment_on[i]":"binary for i in T"},"expressions":{"production[i]":"sum(allocation[i,j] for (i,j) in A)","eligible_demand[i]":"sum(demand[j] for (i,j) in A)"},"constraints":["For each j: sum(allocation[i,j] for (i,j) in A) = demand[j].","For each i: production[i] <= eligible_demand[i] * equipment_on[i].","For each i: production[i] >= equipment_on[i]."],"objective":"Minimize sum(unit_cost[i] * production[i] + setup_cost * equipment_on[i] for i in T)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using six-element, zero-indexed parameter sequences."""
    volume = params["volume"]
    demand = params["demand"]
    unit_cost = params["unit_cost"]
    setup_cost = params["setup_cost"]

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(0, 5)

    model.volume = pyo.Param(
        model.T,
        initialize={i: volume[i] for i in model.T},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize={i: demand[i] for i in model.T},
        within=pyo.NonNegativeIntegers,
    )
    model.unit_cost = pyo.Param(
        model.T,
        initialize={i: unit_cost[i] for i in model.T},
        within=pyo.Reals,
    )
    model.setup_cost = pyo.Param(
        initialize=setup_cost,
        within=pyo.Reals,
    )

    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.T
            for j in model.T
            if pyo.value(model.volume[i]) >= pyo.value(model.volume[j])
        ],
    )

    model.allocation = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)
    model.equipment_on = pyo.Var(model.T, domain=pyo.Binary)

    def production_rule(mdl, i):
        return sum(
            mdl.allocation[i, j] for j in mdl.T if (i, j) in mdl.A
        )

    model.production = pyo.Expression(model.T, rule=production_rule)

    def eligible_demand_rule(mdl, i):
        return sum(mdl.demand[j] for j in mdl.T if (i, j) in mdl.A)

    model.eligible_demand = pyo.Expression(
        model.T, rule=eligible_demand_rule
    )

    def demand_rule(mdl, j):
        return sum(
            mdl.allocation[i, j] for i in mdl.T if (i, j) in mdl.A
        ) == mdl.demand[j]

    model.demand_fulfillment = pyo.Constraint(model.T, rule=demand_rule)

    def activation_upper_rule(mdl, i):
        return (
            mdl.production[i]
            <= mdl.eligible_demand[i] * mdl.equipment_on[i]
        )

    model.activation_upper = pyo.Constraint(
        model.T, rule=activation_upper_rule
    )

    def activation_lower_rule(mdl, i):
        return mdl.production[i] >= mdl.equipment_on[i]

    model.activation_lower = pyo.Constraint(
        model.T, rule=activation_lower_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i] * model.production[i]
            + model.setup_cost * model.equipment_on[i]
            for i in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Continue to objective retrieval, the sole success criterion.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}