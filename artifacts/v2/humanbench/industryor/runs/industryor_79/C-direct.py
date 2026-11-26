import gurobipy as gp
from gurobipy import GRB

def solve(params):
    steel_price         = params["steel_price"]
    engines_price       = params["engines_price"]
    electronics_price   = params["electronics_price"]
    plastics_price      = params["plastics_price"]

    a_steel_engines         = params["a_steel_engines"]
    a_steel_plastics        = params["a_steel_plastics"]
    import_cost_steel       = params["import_cost_steel"]
    labor_steel             = params["labor_steel"]          # person-months

    a_engines_steel         = params["a_engines_steel"]
    a_engines_electronics   = params["a_engines_electronics"]
    a_engines_plastics      = params["a_engines_plastics"]
    import_cost_engines     = params["import_cost_engines"]
    labor_engines           = params["labor_engines"]        # person-years

    a_electronics_steel     = params["a_electronics_steel"]
    a_electronics_engines   = params["a_electronics_engines"]
    a_electronics_plastics  = params["a_electronics_plastics"]
    import_cost_electronics = params["import_cost_electronics"]
    labor_electronics       = params["labor_electronics"]    # person-months

    a_plastics_engines      = params["a_plastics_engines"]
    a_plastics_steel        = params["a_plastics_steel"]
    a_plastics_electronics  = params["a_plastics_electronics"]
    import_cost_plastics    = params["import_cost_plastics"]
    labor_plastics          = params["labor_plastics"]       # person-years

    engine_capacity   = params["engine_capacity"]
    plastics_capacity = params["plastics_capacity"]
    labor_capacity    = params["labor_capacity"]             # person-years

    # Convert person-months to person-years for the labor constraint
    labor_steel_py       = labor_steel / 12.0
    labor_electronics_py = labor_electronics / 12.0

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: total (gross) production of each commodity
    x_steel       = model.addVar(lb=0.0, name="x_steel")
    x_engines     = model.addVar(lb=0.0, name="x_engines")
    x_electronics = model.addVar(lb=0.0, name="x_electronics")
    x_plastics    = model.addVar(lb=0.0, name="x_plastics")

    # Objective: maximize GDP
    # GDP = total export revenues - total import costs - value of intermediate goods consumed
    # For each commodity i:
    #   contribution = price_i * x_i
    #                - import_cost_i * x_i
    #                - sum_j (a_{i,j} * price_j) * x_i   [domestic intermediates valued at world price]
    #
    # Inputs to steel:    engines (a_steel_engines),   plastics (a_steel_plastics)
    # Inputs to engines:  steel   (a_engines_steel),   electronics (a_engines_electronics), plastics (a_engines_plastics)
    # Inputs to electronics: steel (a_electronics_steel), engines (a_electronics_engines), plastics (a_electronics_plastics)
    # Inputs to plastics: engines (a_plastics_engines), steel (a_plastics_steel), electronics (a_plastics_electronics)

    coeff_steel = (steel_price
                   - import_cost_steel
                   - a_steel_engines   * engines_price
                   - a_steel_plastics  * plastics_price)

    coeff_engines = (engines_price
                     - import_cost_engines
                     - a_engines_steel        * steel_price
                     - a_engines_electronics  * electronics_price
                     - a_engines_plastics     * plastics_price)

    coeff_electronics = (electronics_price
                         - import_cost_electronics
                         - a_electronics_steel   * steel_price
                         - a_electronics_engines * engines_price
                         - a_electronics_plastics * plastics_price)

    coeff_plastics = (plastics_price
                      - import_cost_plastics
                      - a_plastics_engines     * engines_price
                      - a_plastics_steel       * steel_price
                      - a_plastics_electronics * electronics_price)

    model.setObjective(
        coeff_steel       * x_steel
        + coeff_engines     * x_engines
        + coeff_electronics * x_electronics
        + coeff_plastics    * x_plastics,
        GRB.MAXIMIZE
    )

    # Material balance: production of each good >= internal use as intermediate input
    # (ensures net exports >= 0, i.e., Carelland doesn't import what it can produce)

    # Steel is used by: engines production, electronics production, plastics production
    model.addConstr(
        x_steel >= a_engines_steel * x_engines
                 + a_electronics_steel * x_electronics
                 + a_plastics_steel * x_plastics,
        name="balance_steel"
    )

    # Engines are used by: steel production, electronics production, plastics production
    model.addConstr(
        x_engines >= a_steel_engines * x_steel
                   + a_electronics_engines * x_electronics
                   + a_plastics_engines * x_plastics,
        name="balance_engines"
    )

    # Electronics are used by: engines production, plastics production
    model.addConstr(
        x_electronics >= a_engines_electronics * x_engines
                        + a_plastics_electronics * x_plastics,
        name="balance_electronics"
    )

    # Plastics are used by: steel production, engines production, electronics production
    model.addConstr(
        x_plastics >= a_steel_plastics * x_steel
                    + a_engines_plastics * x_engines
                    + a_electronics_plastics * x_electronics,
        name="balance_plastics"
    )

    # Capacity constraints
    model.addConstr(x_engines  <= engine_capacity,   name="cap_engines")
    model.addConstr(x_plastics <= plastics_capacity, name="cap_plastics")

    # Labor constraint (all in person-years)
    model.addConstr(
        labor_steel_py       * x_steel
        + labor_engines        * x_engines
        + labor_electronics_py * x_electronics
        + labor_plastics       * x_plastics
        <= labor_capacity,
        name="labor"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}