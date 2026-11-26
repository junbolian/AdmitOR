# IR: {"sets":{"I":[0,1,2],"K":[0,1,2,3,4,5],"C":"K x K x K"},"params":{"r[i,k]":"params['reliability_component1'/'reliability_component2'/'reliability_component3'][k], selected by i","p[i]":"params['unit_price'][i]","w[i]":"params['unit_weight'][i]","B":"params['total_budget']","W":"params['total_weight_limit']"},"variables":{"x[c]":"binary for c in C; selects spare counts (c[0],c[1],c[2])"},"constraints":["sum(c in C) x[c] = 1","sum(c in C) sum(i in I) p[i]*c[i]*x[c] <= B","sum(c in C) sum(i in I) w[i]*c[i]*x[c] <= W"],"objective":"maximize sum(c in C) (product(i in I) r[i,c[i]])*x[c]"}
from itertools import product

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    reliability_data = (
        params["reliability_component1"],
        params["reliability_component2"],
        params["reliability_component3"],
    )
    price_data = params["unit_price"]
    weight_data = params["unit_weight"]
    budget_data = params["total_budget"]
    weight_limit_data = params["total_weight_limit"]

    model = pyo.ConcreteModel()

    model.components = pyo.Set(initialize=range(3), ordered=True)
    model.spare_counts = pyo.Set(initialize=range(6), ordered=True)
    model.configurations = pyo.Set(
        dimen=3,
        initialize=list(product(range(6), repeat=3)),
        ordered=True,
    )

    model.reliability = pyo.Param(
        model.components,
        model.spare_counts,
        initialize={
            (component, count): reliability_data[component][count]
            for component in range(3)
            for count in range(6)
        },
    )
    model.unit_price = pyo.Param(
        model.components,
        initialize={component: price_data[component] for component in range(3)},
    )
    model.unit_weight = pyo.Param(
        model.components,
        initialize={component: weight_data[component] for component in range(3)},
    )
    model.total_budget = pyo.Param(initialize=budget_data)
    model.total_weight_limit = pyo.Param(initialize=weight_limit_data)

    model.selected = pyo.Var(model.configurations, domain=pyo.Binary)

    model.select_one = pyo.Constraint(
        expr=sum(
            model.selected[configuration]
            for configuration in model.configurations
        ) == 1
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(
            sum(
                model.unit_price[component] * configuration[component]
                for component in model.components
            ) * model.selected[configuration]
            for configuration in model.configurations
        ) <= model.total_budget
    )
    model.weight_constraint = pyo.Constraint(
        expr=sum(
            sum(
                model.unit_weight[component] * configuration[component]
                for component in model.components
            ) * model.selected[configuration]
            for configuration in model.configurations
        ) <= model.total_weight_limit
    )

    # Each reliability product is a constant coefficient, so this is a MILP.
    model.system_reliability = pyo.Objective(
        expr=sum(
            pyo.prod(
                model.reliability[component, configuration[component]]
                for component in model.components
            ) * model.selected[configuration]
            for configuration in model.configurations
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.system_reliability))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}