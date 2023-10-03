import earthkit.data

# Change the location of the user defined cache:
earthkit.data.settings.set("user-cache-directory", "/big-disk/earthkit-data-cache")

# Change number of download threads
earthkit.data.settings.set("number-of-download-threads", 7)

# Multiple values can be set together. The argument list
# can be a dictionary:
earthkit.data.settings.set(
    {"number-of-download-threads": 7, "url-download-timeout": "1m"}
)

# Alternatively, we can use keyword arguments. However, because
# the “-” character is not allowed in variable names in Python we have
# to replace “-” with “_” in all the keyword arguments:
earthkit.data.settings.set(number_of_download_threads=8, url_download_timeout="2m")
