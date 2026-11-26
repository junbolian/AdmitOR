# IR: {"sets":{"P":["chicken","salmon","tofu"],"V":[0,1,2]},"params":["protein_chicken","protein_salmon","protein_tofu","price_chicken","price_salmon","price_tofu","budget","max_weight"],"variables":{"protein_weight[P]":"NonNegativeReals, grams","protein_selected[P]":"Binary","vegetable_selected[V]":"Binary"},"constraints":["sum(protein_selected[p] for p in P) == 1","protein_weight[p] <= max_weight * protein_selected[p] for p in P","sum(vegetable_selected[v] for v in V) >= 3","sum(protein_weight[p] for p in P) <= max_weight","sum(price[p] * protein_weight[p] / 100 for p in P) <= budget"],"objective":"maximize sum(protein[p] * protein_weight[p] / 100 for p in P)","assumptions":["V represents three distinct previously considered vegetable types.","Vegetables are represented by selection indicators only because their weights, prices, nutritional values, and minimum servings are unspecified.","Budget and weight constraints therefore apply only to the quantified protein foods; the full dinner optimum cannot be determined from the supplied parameters."]}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    protein = {
        "chicken": params["protein_chicken"],
        "salmon": params["protein_salmon"],
        "tofu": params["protein_tofu"],
    }
    price = {
        "chicken": params["price_chicken"],
        "salmon": params["price_salmon"],
        "tofu": params["price_tofu"],
    }
    budget = params["budget"]
    max_weight = params["max_weight"]

    # The factor 100 is a unit conversion, not an assumed input value.
    # No vegetable costs, weights, or protein values are fabricated.
    model = pyo.ConcreteModel()
    model.protein_sources = pyo.Set(initialize=tuple(protein))
    model.vegetable_types = pyo.Set(initialize=range(3))

    model.protein_weight = pyo.Var(
        model.protein_sources,
        domain=pyo.NonNegativeReals,
    )
    model.protein_selected = pyo.Var(
        model.protein_sources,
        domain=pyo.Binary,
    )
    model.vegetable_selected = pyo.Var(
        model.vegetable_types,
        domain=pyo.Binary,
    )

    model.one_protein_source = pyo.Constraint(
        expr=sum(
            model.protein_selected[source]
            for source in model.protein_sources
        ) == 1
    )

    def protein_link_rule(instance, source):
        return (
            instance.protein_weight[source]
            <= max_weight * instance.protein_selected[source]
        )

    model.protein_selection_link = pyo.Constraint(
        model.protein_sources,
        rule=protein_link_rule,
    )

    model.minimum_vegetable_types = pyo.Constraint(
        expr=sum(
            model.vegetable_selected[vegetable]
            for vegetable in model.vegetable_types
        ) >= 3
    )

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.protein_weight[source]
            for source in model.protein_sources
        ) <= max_weight
    )

    model.budget_limit = pyo.Constraint(
        expr=sum(
            price[source] * model.protein_weight[source] / 100
            for source in model.protein_sources
        ) <= budget
    )

    model.total_protein = pyo.Objective(
        expr=sum(
            protein[source] * model.protein_weight[source] / 100
            for source in model.protein_sources
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Other runtime errors remain visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    # Success depends exclusively on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_protein))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}