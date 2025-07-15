```r
library(dplyr)
library(stringr)
library(lubridate)

# Extract the values in the 'period_name' column to process
period_values <- df$period_name

# Initialize empty vectors to store month, year, and year_month ("YYYY-MM") values
month_vec <- integer(length(period_values))
year_vec <- integer(length(period_values))
year_month_vec <- character(length(period_values))

# Loop through each value in the 'period_name' column
for (i in seq_along(period_values)) {
  
  # Clean up the string by trimming spaces
  val <- stringr::str_trim(period_values[i])
  
  # Initialize temporary variables for each value
  m <- NA_integer_
  y <- NA_integer_
  ym_str <- NA_character_
  
  # Check for missing or empty values
  if (is.na(val) || val == "") {
    dt <- NA

  # Format: "Jan-2015"
  } else if (nchar(val) == 8 && substr(val, 4,4) == "-") {
    dt <- tryCatch(lubridate::parse_date_time(val, "b-Y"), error = function(e) NA)

  # Format: "Jan 2015"
  } else if (nchar(val) == 8 && substr(val, 4,4) == " ") {
    dt <- tryCatch(lubridate::parse_date_time(val, "b Y"), error = function(e) NA)

  # Format: "January-2015"
  } else if (stringr::str_detect(val, "-") && nchar(stringr::word(val, 1, sep = "-")) > 3) {
    dt <- tryCatch(lubridate::parse_date_time(val, "B-Y"), error = function(e) NA)

  # Format: "January 2015"
  } else if (stringr::str_detect(val, " ") && nchar(stringr::word(val, 1, sep = " ")) > 3) {
    dt <- tryCatch(lubridate::parse_date_time(val, "B Y"), error = function(e) NA)

  # Format: "01-2015"
  } else if (stringr::str_detect(val, "-") && grepl("^[0-9]{2}-[0-9]{4}$", val)) {
    dt <- tryCatch(lubridate::parse_date_time(val, "m-Y"), error = function(e) NA)

  # Format: "01/2015"
  } else if (stringr::str_detect(val, "/") && grepl("^[0-9]{2}/[0-9]{4}$", val)) {
    dt <- tryCatch(lubridate::parse_date_time(val, "m/Y"), error = function(e) NA)

  # Format: "01.2015"
  } else if (stringr::str_detect(val, "\\.") && grepl("^[0-9]{2}\\.[0-9]{4}$", val)) {
    dt <- tryCatch(lubridate::parse_date_time(val, "m.Y"), error = function(e) NA)

  # Format: "2015-01"
  } else if (stringr::str_detect(val, "-") && grepl("^[0-9]{4}-[0-9]{2}$", val)) {
    dt <- tryCatch(lubridate::parse_date_time(val, "Y-m"), error = function(e) NA)

  # Format: "2015/01"
  } else if (stringr::str_detect(val, "/") && grepl("^[0-9]{4}/[0-9]{2}$", val)) {
    dt <- tryCatch(lubridate::parse_date_time(val, "Y/m"), error = function(e) NA)

  # Format: "2015.01"
  } else if (stringr::str_detect(val, "\\.") && grepl("^[0-9]{4}\\.[0-9]{2}$", val)) {
    dt <- tryCatch(lubridate::parse_date_time(val, "Y.m"), error = function(e) NA)

  # Format: "2015 Jan"
  } else if (length(stringr::str_split(val, " ", simplify = TRUE)) == 2 && grepl("^[0-9]{4}", val)) {
    dt <- tryCatch(lubridate::parse_date_time(val, "Y b"), error = function(e) NA)

  # Format: "2015 January"
  } else if (length(stringr::str_split(val, " ", simplify = TRUE)) == 2 && grepl("^[0-9]{4}", val)) {
    dt <- tryCatch(lubridate::parse_date_time(val, "Y B"), error = function(e) NA)

  # Format: "January2015"
  } else if (stringr::str_detect(val, "^[A-Za-z]{3,}[0-9]{4}$")) {
    dt <- tryCatch(lubridate::parse_date_time(val, "BY"), error = function(e) NA)

  # Format: "Jan2015"
  } else if (stringr::str_detect(val, "^[A-Za-z]{3}[0-9]{4}$")) {
    dt <- tryCatch(lubridate::parse_date_time(val, "bY"), error = function(e) NA)

  # Format: "201501"
  } else if (nchar(val) == 6 && grepl("^[0-9]{6}$", val)) {
    dt <- tryCatch(lubridate::parse_date_time(val, "Ym"), error = function(e) NA)

  # Format: "012015"
  } else if (nchar(val) == 6 && grepl("^[0-9]{6}$", val)) {
    dt <- tryCatch(lubridate::parse_date_time(val, "mY"), error = function(e) NA)

  # Format not recognized
  } else {
    dt <- NA
  }

  # If parsing succeeded, extract month and year, and build "YYYY-MM" string
  if (!is.na(dt)) {
    m <- lubridate::month(dt)
    y <- lubridate::year(dt)
    ym_str <- sprintf("%04d-%02d", y, m)
  }

  # Save values into pre-created vectors
  month_vec[i] <- m
  year_vec[i] <- y
  year_month_vec[i] <- ym_str
}

# Add extracted values as new columns in the dataframe
df <- df |>
  dplyr::mutate(
    month = month_vec,
    year = year_vec,
    year_month = year_month_vec
  )
```
