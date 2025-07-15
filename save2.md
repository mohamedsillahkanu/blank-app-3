```r
library(dplyr)  # For data manipulation
library(rio)    # For easy export to multiple file formats
library(here)   # For constructing file paths

df <- dhis2_df  # Your main dataset

# Function to aggregate and save data for a given set of grouping variables
save_aggregated_data <- function(df, group_vars, save_path) {
  
  # Check if all required grouping columns exist in the dataset
  if (!all(group_vars %in% names(df))) {
    # If any grouping column is missing, print a message and skip processing
    message("Skipping ", paste(tail(group_vars, 1)), ": one or more required columns are missing.")
    return(NULL)  # Exit function early
  }
  
  # Perform aggregation:
  # - Group data by the specified grouping variables
  # - Sum all numeric columns within each group, ignoring NA values
  aggregated <- df |>
    dplyr::group_by(across(all_of(group_vars))) |>
    dplyr::summarise(
      dplyr::across(
        dplyr::where(is.numeric),
        \(x) sum(x, na.rm = TRUE)
      ),
      .groups = "drop"
    )
  
  # Determine the level name from the last grouping variable (e.g., "adm1", "adm2", "hf")
  level_name <- tail(group_vars, 1)
  
  # Construct a base filename to use for saving files
  base_filename <- paste0("aggregated_data_monthly_", level_name, "_data")
  
  # Export aggregated data to multiple formats in the specified save_path
  rio::export(aggregated, here::here(save_path, paste0(base_filename, ".xlsx")))
  rio::export(aggregated, here::here(save_path, paste0(base_filename, ".csv")))
  rio::export(aggregated, here::here(save_path, paste0(base_filename, ".dta")))
  
  # Print a success message after saving
  message("Saved aggregated data for ", level_name)
}

# Define grouping columns needed for each administrative level aggregation
levels <- list(
  adm1 = c("adm0", "adm1", "year", "month"),
  adm2 = c("adm0", "adm1", "adm2", "year", "month"),
  adm3 = c("adm0", "adm1", "adm2", "adm3", "year", "month"),
  adm4 = c("adm0", "adm1", "adm2", "adm3", "adm4", "year", "month"),
  hf   = c("adm0", "adm1", "adm2", "adm3", "adm4", "hf", "year", "month")
)
```

# Loop through each admin level and run the aggregation + export function
for (lvl in names(levels)) {
  save_aggregated_data(df, levels[[lvl]], save_path)
}
