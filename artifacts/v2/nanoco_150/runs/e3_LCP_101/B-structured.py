# IR: {"sets":{"C":"range(num_cells)","B":"range(num_frequency_bands), interpreted as a cardinality","E":"range(num_links)","A":"{(c,b): c in C, b in frequency_pools[c]}"},"params":["num_cells","num_links","interference_links","frequency_pools","num_frequency_bands"],"variables":{"x[c,b]":"binary for c in C, b in B; fixed to zero when (c,b) not in A","maximum_band":"nonnegative integer"},"constraints":["For every c in C: sum(b in B, x[c,b]) = 1.","For every e in E with endpoints (u,v), and b in B: x[u,b] + x[v,b] <= 1.","For every c in C: maximum_band >= sum(b in B, b*x[c,b])."],"objective":"Minimize maximum_band."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cells = params["num_cells"]
    num_links = params["num_links"]
    interference_links = list(params["interference_links"])
    frequency_pools = params["frequency_pools"]
    num_frequency_bands = params["num_frequency_bands"]

    if num_cells <= 0 or num_frequency_bands <= 0 or num_links < 0:
        return {"objective": None, "status": "invalid_dimensions"}

    if len(interference_links) != num_links:
        return {"objective": None, "status": "invalid_link_count"}

    authorized = {
        cell: set(frequency_pools[cell])
        for cell in range(num_cells)
    }

    for cell in range(num_cells):
        if any(
            band not in range(num_frequency_bands)
            for band in authorized[cell]
        ):
            return {"objective": None, "status": "invalid_frequency_pool"}

    for endpoints in interference_links:
        if len(endpoints) != 2:
            return {"objective": None, "status": "invalid_link"}
        if any(endpoint not in range(num_cells) for endpoint in endpoints):
            return {"objective": None, "status": "invalid_link"}

    model = pyo.ConcreteModel()
    model.cells = pyo.Set(initialize=range(num_cells), ordered=True)
    model.bands = pyo.Set(initialize=range(num_frequency_bands), ordered=True)
    model.link_ids = pyo.Set(initialize=range(num_links), ordered=True)

    model.assignment = pyo.Var(
        model.cells, model.bands, domain=pyo.Binary
    )
    model.maximum_band = pyo.Var(domain=pyo.NonNegativeIntegers)

    for cell in model.cells:
        for band in model.bands:
            if band not in authorized[cell]:
                model.assignment[cell, band].fix(0)

    def exactly_one_rule(instance, cell):
        return pyo.quicksum(
            instance.assignment[cell, band] for band in instance.bands
        ) == 1

    model.exactly_one = pyo.Constraint(
        model.cells, rule=exactly_one_rule
    )

    def interference_rule(instance, link_id, band):
        first_cell, second_cell = interference_links[link_id]
        return (
            instance.assignment[first_cell, band]
            + instance.assignment[second_cell, band]
            <= 1
        )

    model.interference_limits = pyo.Constraint(
        model.link_ids, model.bands, rule=interference_rule
    )

    def maximum_band_rule(instance, cell):
        return instance.maximum_band >= pyo.quicksum(
            band * instance.assignment[cell, band]
            for band in instance.bands
        )

    model.maximum_band_limits = pyo.Constraint(
        model.cells, rule=maximum_band_rule
    )
    model.total_objective = pyo.Objective(
        expr=model.maximum_band, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Leave other, unexpected runtime errors visible to the harness.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}