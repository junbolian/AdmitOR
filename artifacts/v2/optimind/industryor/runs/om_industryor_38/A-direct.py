import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Read params
    p_steel = params["price_steel"]
    p_eng = params["price_engines"]
    p_elec = params["price_electronics"]
    p_plast = params["price_plastic"]

    s_req_eng = params["steel_req_engines"]
    s_req_plast = params["steel_req_plastic"]
    s_imp = params["steel_import_cost"]
    s_lab = params["steel_labor"]

    e_req_steel = params["engines_req_steel"]
    e_req_elec = params["engines_req_electronics"]
    e_req_plast = params["engines_req_plastic"]
    e_imp = params["engines_import_cost"]
    e_lab = params["engines_labor"]

    el_req_steel = params["electronics_req_steel"]
    el_req_eng = params["electronics_req_engines"]
    el_req_plast = params["electronics_req_plastic"]
    el_imp = params["electronics_import_cost"]
    el_lab = params["electronics_labor"]

    pl_req_eng = params["plastic_req_engines"]
    pl_req_steel = params["plastic_req_steel"]
    pl_req_elec = params["plastic_req_electronics"]
    pl_imp = params["plastic_import_cost"]
    pl_lab = params["plastic_labor"]

    cap_eng = params["cap_engines"]
    cap_plast = params["cap_plastic"]
    labor_avail = params["labor_available"]

    model = pyo.ConcreteModel()

    # Decision variables: production quantities (>= 0)
    model.x_steel = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_eng = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_elec = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_plast = pyo.Var(domain=pyo.NonNegativeReals)

    # Capacity constraints
    model.cap_eng = pyo.Constraint(expr=model.x_eng <= cap_eng)
    model.cap_plast = pyo.Constraint(expr=model.x_plast <= cap_plast)

    # Labor constraint
    model.labor = pyo.Constraint(
        expr=s_lab * model.x_steel
        + e_lab * model.x_eng
        + el_lab * model.x_elec
        + pl_lab * model.x_plast
        <= labor_avail
    )

    # Balance constraints for each commodity (gross production + nothing imported
    # in intermediates allowed to be imported; domestic production must cover
    # own intermediate consumption, rest exported). The net export of each
    # commodity is production minus intermediate use. Since production is
    # NonNegativeReals and intermediates are consumed, we require production
    # of each commodity at least equals its intermediate requirement; exports
    # are the surplus.

    # Steel: consumed by engines, electronics, plastic
    model.bal_steel = pyo.Constraint(
        expr=model.x_steel
        >= e_req_steel * model.x_eng
        + el_req_steel * model.x_elec
        + pl_req_steel * model.x_plast
    )

    # Engines: consumed by steel, electronics, plastic
    model.bal_eng = pyo.Constraint(
        expr=model.x_eng
        >= s_req_eng * model.x_steel
        + el_req_eng * model.x_elec
        + pl_req_eng * model.x_plast
    )

    # Electronics: consumed by engines, plastic
    model.bal_elec = pyo.Constraint(
        expr=model.x_elec
        >= e_req_elec * model.x_eng + pl_req_elec * model.x_plast
    )

    # Plastic: consumed by steel, engines, electronics
    model.bal_plast = pyo.Constraint(
        expr=model.x_plast
        >= s_req_plast * model.x_steel
        + e_req_plast * model.x_eng
        + el_req_plast * model.x_elec
    )

    # Objective: maximize GDP = total value of exports minus imported goods cost
    # Exports of steel:
    #   x_steel - (e_req_steel*x_eng + el_req_steel*x_elec + pl_req_steel*x_plast)
    # times price, etc. Imports = import cost coefficients times production.
    # Note: imported goods are a cost for producing each unit (used in production),
    # they do not affect the balance of domestic commodities (treated as separate input).

    export_steel = (
        model.x_steel
        - e_req_steel * model.x_eng
        - el_req_steel * model.x_elec
        - pl_req_steel * model.x_plast
    )
    export_eng = (
        model.x_eng
        - s_req_eng * model.x_steel
        - el_req_eng * model.x_elec
        - pl_req_eng * model.x_plast
    )
    export_elec = (
        model.x_elec
        - e_req_elec * model.x_eng
        - pl_req_elec * model.x_plast
    )
    export_plast = (
        model.x_plast
        - s_req_plast * model.x_steel
        - e_req_plast * model.x_eng
        - el_req_plast * model.x_elec
    )

    imports_cost = (
        s_imp * model.x_steel
        + e_imp * model.x_eng
        + el_imp * model.x_elec
        + pl_imp * model.x_plast
    )

    model.obj = pyo.Objective(
        expr=p_steel * export_steel
        + p_eng * export_eng
        + p_elec * export_elec
        + p_plast * export_plast
        - imports_cost,
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}