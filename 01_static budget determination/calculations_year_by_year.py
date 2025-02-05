# Global budget for reaching 1.7 °C with a probability of 83 % is 550 Gt CO2.
# Deducting the emissions from 2020 to 2024 to get a budget for 2025.
# Using the factor of 0.887 (Share of CO2 on German greenhouse gas (GHG) emissions) to get a GHG budget instead of CO2 budget.
GB = (550 - 185) / 0.887

Fn = 0.0106     # Allocation factor from global to national level (Allocation approach: "Equality")
Fb = 0.303      # Share of the building sector on national emissions in Germany
Fe = 0.3707     # Average share of embodied emissions on the emissions of the building sector (Yearly average from 2025 to 2045)
Fo = 1 - Fe     # Average share of operational emissions on the emissions of the building sector (Yearly average from 2025 to 2045)

rn = 0.009  # Yearly new-built rate
rd = 0.001  # Yearly demolition rate
rr = 0.01   # Yearly renovation rate

year_GHG_neutrality = 2045 # Year of GHG neutrality in Germany


# Residential net room area in m²: First the residential living area minus residential areas in non-residential buildings 
# (already included in non-residential net room area) (Destatis (2024), Destatis (2024b)). Only data for the living area is 
# available that is why it needs to be multiplied with two factors to first calculate the gross floor area (1.87) and then
# deduct the construction area (0.83) (BKI Baukosten Gebäude Neubau (2024), p. 97, p.100) to get the net room area for 
# residential buildings in m²:

Ae_residential = (4024768000 - 127039000) * 1.87 * 0.83

# Non-residential net room area that is relevant to the German Building Energy Act (GEG) in m² from Hörner et al. (2024, https://doi.org/10.1016/j.buildenv.2024.111407):

Ae_nonresidential = 3073000000 

Ae_initial = Ae_residential + Ae_nonresidential # Total area of the German building stock that is relevant to the GEG

def calculate_emissions_year_by_year():

    # Calculates building area and emissions per year from 2025 up to 'year_GHG_neutrality' (e.g., 2045).

    # Steps:
    # 1) Pre-correction for the period 2021–2025.
    # 2) Year-by-year calculation of:
    #   - Total building area
    #   - Newly added building area
    #   - Operational emissions
    #   - Embodied emissions

    # 1) Pre-correction for the period 2021–2025
    years_pre = 2025 - 2021  # Number of years before 2025 we want to account for
    Ae_temp = Ae_initial

    for _ in range(years_pre):
        # Estimate new construction and demolition in each of those pre-years
        pre_An = rn * Ae_temp  # New construction
        pre_Ad = rd * Ae_temp  # Demolition
        Ae_temp += pre_An - pre_Ad

    # Building area in 2025 (after pre-correction)
    Ae_2025 = Ae_temp

    # 2) Initialize lists to store yearly results
    years = list(range(2025, year_GHG_neutrality + 1))  # from 2025 to 'year_GHG_neutrality'
    Ae_list = []      # Total building area per year
    Anew_list = []    # Newly added (An + Ar) building area per year
    op_em_list = []   # Operational emissions per year
    emb_em_list = []  # Embodied emissions per year

    Ae_current = Ae_2025

    # Total budget for operational GHG emissions in Germany
    share_operational = GB * Fn * Fb * Fo * 1e12  # kg CO2e (instead of Gt)

    # Total budget for embodied GHG emissions in Germany 
    share_embodied = GB * Fn * Fb * Fe * 1e12  # kg CO2e (instead of Gt)

    for year in years:
        # Annual new construction, demolition, and renovation area
        An = rn * Ae_current
        Ad = rd * Ae_current
        Ar = rr * Ae_current

        # Update total building area for the next year
        Ae_current += An - Ad

        # Newly added area = new construction + renovation
        A_new = An + Ar

        # Operational emissions per year for the existing total building area per m²
        # Divided by 21 to spread over 2025–2045 (21 years, including 2025), as an example
        E_op = share_operational / (year_GHG_neutrality + 1 - 2025) / Ae_current  # kg CO2e per year and per m²

        # Embodied emissions per year  per m² (new construction + renovation) and distributed over a life-cycle of 50 years
        E_emb = share_embodied / (year_GHG_neutrality + 1 - 2025) / A_new / 50  # kg CO2e per year and per m²

        # Store values in the lists
        Ae_list.append(Ae_current)
        Anew_list.append(A_new)
        op_em_list.append(E_op)
        emb_em_list.append(E_emb)

    return years, Ae_list, Anew_list, op_em_list, emb_em_list


# Call the function
years, Ae_per_year, Anew_per_year, op_em, emb_em = calculate_emissions_year_by_year()

# Sum up emissions over the period 2025–2045
total_op_em = sum(op_em)
total_emb_em = sum(emb_em)

# Calculate the average emissions per m² and per year
print(f"\nAverage operational emissions from 2025–{year_GHG_neutrality}: "
      f"{total_op_em / (year_GHG_neutrality + 1 - 2025):.2f} kgCO2e/(m²*a)")
print(f"Average embodied emissions from 2025–{year_GHG_neutrality}: "
      f"{total_emb_em / (year_GHG_neutrality + 1 - 2025):.2f} kgCO2e/(m²*a)")

