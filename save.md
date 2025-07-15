library(dplyr)
library(rio)
library(here)

df <- dhis2_df  # Your dataset

# --------------------------
# ADM1 level
# --------------------------
if (all(c("adm0", "adm1", "year", "month") %in% names(df))) {
  # If all columns needed for ADM1 level grouping exist,
  # group by adm0, adm1, year, and month, and sum numeric columns
  adm1_monthly <- df |>
    dplyr::group_by(adm0, adm1, year, month) |>
    dplyr::summarise(
      dplyr::across(dplyr::where(is.numeric), \(x) sum(x, na.rm = TRUE)),
      .groups = "drop"
    )
  
  rio::export(adm1_monthly, here::here(save_path, "aggregated_data_monthly_adm1_data.xlsx"))
  rio::export(adm1_monthly, here::here(save_path, "aggregated_data_monthly_adm1_data.csv"))
  rio::export(adm1_monthly, here::here(save_path, "aggregated_data_monthly_adm1_data.dta"))
} else {
  message("Skipping adm1: one or more required columns are missing.")
}

# --------------------------
# ADM2 level
# --------------------------
if (all(c("adm0", "adm1", "adm2", "year", "month") %in% names(df))) {
  # If all columns needed for ADM2 level grouping exist,
  # group by adm0, adm1, adm2, year, and month, and sum numeric columns
  adm2_monthly <- df |>
    dplyr::group_by(adm0, adm1, adm2, year, month) |>
    dplyr::summarise(
      dplyr::across(dplyr::where(is.numeric), \(x) sum(x, na.rm = TRUE)),
      .groups = "drop"
    )
  
  rio::export(adm2_monthly, here::here(save_path, "aggregated_data_monthly_adm2_data.xlsx"))
  rio::export(adm2_monthly, here::here(save_path, "aggregated_data_monthly_adm2_data.csv"))
  rio::export(adm2_monthly, here::here(save_path, "aggregated_data_monthly_adm2_data.dta"))
} else {
  message("Skipping adm2: one or more required columns are missing.")
}

# --------------------------
# ADM3 level
# --------------------------
if (all(c("adm0", "adm1", "adm2", "adm3", "year", "month") %in% names(df))) {
  # If all columns needed for ADM3 level grouping exist,
  # group by adm0, adm1, adm2, adm3, year, and month, and sum numeric columns
  adm3_monthly <- df |>
    dplyr::group_by(adm0, adm1, adm2, adm3, year, month) |>
    dplyr::summarise(
      dplyr::across(dplyr::where(is.numeric), \(x) sum(x, na.rm = TRUE)),
      .groups = "drop"
    )
  
  rio::export(adm3_monthly, here::here(save_path, "aggregated_data_monthly_adm3_data.xlsx"))
  rio::export(adm3_monthly, here::here(save_path, "aggregated_data_monthly_adm3_data.csv"))
  rio::export(adm3_monthly, here::here(save_path, "aggregated_data_monthly_adm3_data.dta"))
} else {
  message("Skipping adm3: one or more required columns are missing.")
}

# --------------------------
# ADM4 level
# --------------------------
if (all(c("adm0", "adm1", "adm2", "adm3", "adm4", "year", "month") %in% names(df))) {
  # If all columns needed for ADM4 level grouping exist,
  # group by adm0, adm1, adm2, adm3, adm4, year, and month, and sum numeric columns
  adm4_monthly <- df |>
    dplyr::group_by(adm0, adm1, adm2, adm3, adm4, year, month) |>
    dplyr::summarise(
      dplyr::across(dplyr::where(is.numeric), \(x) sum(x, na.rm = TRUE)),
      .groups = "drop"
    )
  
  rio::export(adm4_monthly, here::here(save_path, "aggregated_data_monthly_adm4_data.xlsx"))
  rio::export(adm4_monthly, here::here(save_path, "aggregated_data_monthly_adm4_data.csv"))
  rio::export(adm4_monthly, here::here(save_path, "aggregated_data_monthly_adm4_data.dta"))
} else {
  message("Skipping adm4: one or more required columns are missing.")
}

# --------------------------
# HF (Health Facility) level
# --------------------------
if (all(c("adm0", "adm1", "adm2", "adm3", "adm4", "hf", "year", "month") %in% names(df))) {
  # If all columns needed for HF level grouping exist,
  # group by adm0, adm1, adm2, adm3, adm4, hf, year, and month, and sum numeric columns
  hf_monthly <- df |>
    dplyr::group_by(adm0, adm1, adm2, adm3, adm4, hf, year, month) |>
    dplyr::summarise(
      dplyr::across(dplyr::where(is.numeric), \(x) sum(x, na.rm = TRUE)),
      .groups = "drop"
    )
  
  rio::export(hf_monthly, here::here(save_path, "aggregated_data_monthly_hf_data.xlsx"))
  rio::export(hf_monthly, here::here(save_path, "aggregated_data_monthly_hf_data.csv"))
  rio::export(hf_monthly, here::here(save_path, "aggregated_data_monthly_hf_data.dta"))
} else {
  message("Skipping hf: one or more required columns are missing.")
}
