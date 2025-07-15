```r
library(dplyr)
library(stringr)
library(lubridate)

# Assume df is your dataframe with a column named 'period_name' containing various date formats

period_values <- df$period_name

# Initialize vectors to store extracted month, year, and year_month (character string "YYYY-MM")
month_vec <- integer(length(period_values))
year_vec <- integer(length(period_values))
year_month_vec <- character(length(period_values))  # To hold "YYYY-MM" strings

for (i in seq_along(period_values)) {
  
  val <- stringr::str_trim(period_values[i])  # Trim whitespace
  
  m <- NA_integer_   # Default month as NA
  y <- NA_integer_   # Default year as NA
  ym_str <- NA_character_  # Default year_month as NA string
  
  # Skip empty or NA values
  if (is.na(val) || val == "") {
    # Do nothing, leave NA
    
  # Below are multiple date format checks using if-else conditions
  # Each block tries to parse the string val with a specific known format using lubridate::parse_date_time()
  # Example: "Jan-2015", "01/2015", "2015-01", "January2015", "201501", etc.
  
  } else if (nchar(val) == 8 && substr(val, 4,4) == "-") {        # Format example: "Jan-2015"
    dt <- tryCatch(lubridate::parse_date_time(val, "b-Y"), error = function(e) NA)
    
  } else if (nchar(val) == 8 && substr(val, 4,4) == " ") {        # Format example: "Jan 2015"
    dt <- tryCatch(lubridate::parse_date_time(val, "b Y"), error = function(e) NA)
    
  } else if (stringr::str_detect(val, "-") && nchar(stringr::word(val, 1, sep = "-")) > 3) {  # "January-2015"
    dt <- tryCatch(lubridate::parse_date_time(val, "B-Y"), error = function(e) NA)
    
  } else if (stringr::str_detect(val, " ") && nchar(stringr::word(val, 1, sep = " ")) > 3) {  # "January 2015"
    dt <- tryCatch(lubridate::parse_date_time(val, "B Y"), error = function(e) NA)
    
  } else if (stringr::str_detect(val, "-") && grepl("^[0-9]{2}-[0-9]{4}$", val)) {            # "01-2015"
    dt <- tryCatch(lubridate::parse_date_time(val, "m-Y"), error = function(e) NA)
    
  } else if (stringr::str_detect(val, "/") && grepl("^[0-9]{2}/[0-9]{4}$", val)) {            # "01/2015"
    dt <- tryCatch(lubridate::parse_date_time(val, "m/Y"), error = function(e) NA)
    
  } else if (stringr::str_detect(val, "\\.") && grepl("^[0-9]{2}\\.[0-9]{4}$", val)) {        # "01.2015"
    dt <- tryCatch(lubridate::parse_date_time(val, "m.Y"), error = function(e) NA)
    
  } else if (stringr::str_detect(val, "-") && grepl("^[0-9]{4}-[0-9]{2}$", val)) {            # "2015-01"
    dt <- tryCatch(lubridate::parse_date_time(val, "Y-m"), error = function(e) NA)
    
  } else if (stringr::str_detect(val, "/") && grepl("^[0-9]{4}/[0-9]{2}$", val)) {            # "2015/01"
    dt <- tryCatch(lubridate::parse_date_time(val, "Y/m"), error = function(e) NA)
    
  } else if (stringr::str_detect(val, "\\.") && grepl("^[0-9]{4}\\.[0-9]{2}$", val)) {        # "2015.01"
    dt <- tryCatch(lubridate::parse_date_time(val, "Y.m"), error = function(e) NA)
    
  } else if (length(stringr::str_split(val, " ", simplify = TRUE)) == 2 && grepl("^[0-9]{4}", val)) {  # "2015 Jan"
    dt <- tryCatch(lubridate::parse_date_time(val, "Y b"), error = function(e) NA)
    
  } else if (length(stringr::str_split(val, " ", simplify = TRUE)) == 2 && grepl("^[0-9]{4}", val)) {  # "2015 January"
    dt <- tryCatch(lubridate::parse_date_time(val, "Y B"), error = function(e) NA)
    
  } else if (stringr::str_detect(val, "^[A-Za-z]{3,}[0-9]{4}$")) {                             # "January2015"
    dt <- tryCatch(lubridate::parse_date_time(val, "BY"), error = function(e) NA)
    
  } else if (stringr::str_detect(val, "^[A-Za-z]{3}[0-9]{4}$")) {                              # "Jan2015"
    dt <- tryCatch(lubridate::parse_date_time(val, "bY"), error = function(e) NA)
    
  } else if (nchar(val) == 6 && grepl("^[0-9]{6}$", val)) {                                   # "201501"
    dt <- tryCatch(lubridate::parse_date_time(val, "Ym"), error = function(e) NA)
    
  } else if (nchar(val) == 6 && grepl("^[0-9]{6}$", val)) {                                   # "012015"
    dt <- tryCatch(lubridate::parse_date_time(val, "mY"), error = function(e) NA)
    
  } else {
    dt <- NA  # If no format matched, assign NA
  }
  
  # If parsing succeeded, extract month and year, and build "YYYY-MM" string
  if (!is.na(dt)) {
    m <- lubridate::month(dt)    # Extract numeric month (1-12)
    y <- lubridate::year(dt)     # Extract year (e.g., 2015)
    
    # Create year-month string in "YYYY-MM" format (no day)
    ym_str <- sprintf("%04d-%02d", y, m)
  }
  
  # Save extracted values into corresponding vectors
  month_vec[i] <- m          # Store month
  year_vec[i] <- y           # Store year
  year_month_vec[i] <- ym_str  # Store "YYYY-MM" string
}

# Add new columns to df using dplyr::mutate() and pipe operator
df <- df |>
  dplyr::mutate(
    month = month_vec,           # Numeric month (1-12)
    year = year_vec,             # Numeric year (e.g., 2015)
    year_month = year_month_vec  # Character year-month string "YYYY-MM"
  )
```
